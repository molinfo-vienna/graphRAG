import os
os.environ['HF_HOME'] = '/data/local/sschoendorfer'
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from huggingface_hub import hf_hub_download
from neo4j import GraphDatabase
from transformers import AutoTokenizer, pipeline
import torch
import pandas as pd
import json

# Base idea from this article: 
# https://medium.com/@silviaonofrei/code-llamas-knowledge-of-neo4j-s-cypher-query-language-54783d2ad421

def read_query(driver, query, params=None):
    with driver.session() as session:
            result = session.run(query, params)
            output = [r.values() for r in result]
            output.insert(0, result.keys())
            return output
    
def generate_answer_qwen(user_prompt, system_prompt, pipe, **kwargs):
    # Use a more natural instruction format for Qwen-Chat or Qwen-Instruct
    full_prompt = f"System: {system_prompt}\nUser: {user_prompt}\nAssistant:"
 

    # Set a default max_new_tokens if not provided
    if "max_new_tokens" not in kwargs:
        kwargs["max_new_tokens"] = 512

    # Generate the output using the pipeline
    output = pipe(full_prompt,
                  do_sample=True,
                  top_k=10,
                  top_p=0.95,
                  **kwargs)
    
    # Extract the relevant part of the generated text
    output = output[0]["generated_text"]
    return output.split('Assistant:', 1)[1].strip()
    
def generate_answer_code_llama(user_prompt, system_prompt, pipe, **kwargs):
    full_prompt = "<s>[INST]<<SYS>>\n{system}\n<</SYS>>\n\n{user}[/INST]\n\n".format(system=f"{system_prompt}",
                                                                        user=f'{user_prompt}')

    # The default max length is pretty small, increase the threshold
    if "max_new_tokens" not in kwargs:
        kwargs["max_new_tokens"] = 512
    
    kwargs.setdefault("temperature", 0.7)

    output = pipe(full_prompt,
                      do_sample=True,
                      top_k=5,
                      top_p=0.9,
                      **kwargs)
    
    output = output[0]["generated_text"]
    return output.split('<</SYS>>', 1)[1].split("[/INST]")[1]

def format_system_prompt(system_prompt):
    return system_prompt.replace("{", "{{").replace("}", "}}") 

def schema_text(node_props, rels):
    return f"""
    Node properties are the following:
    {node_props}
    Relationship point from source to target nodes
    {rels}
    """

def generate_cypher_query_prompt(schema):
    return """
    You are experienced with cypher queries. Provide answers in Cypher query language, *strictly* based on the following graph Neo4j schema. Respect the possible direction of relationships and the possible naming of nodes, properties and relationships. Only answer with the query and nothing else.

    ### The Schema

    {schema}

    ### Examples 
    Q: What methods does AromaticSubstructure have?
    A: MATCH (c:Class {{name: 'AromaticSubstructure'}})-[:HAS]->(f:Function) RETURN f.name, f.comment

    Q: What does the class AtomPredicate do?
    A: MATCH (c:Class {{name: "AtomPredicate"}}) RETURN c.comment
    """.format(schema = schema) 

def generate_rag_prompt(retrieved_context, cypher_query):
    return """

    You are a highly intelligent assistant. Your job is to answer user questions using *only* the information from the retrieved context provided from a Neo4j knowledge graph database. 
    The retrieved context is the result of a cypher query.
    Ensure that your response strictly relies on the retrieved context, and do not add any information from other sources.

    Cypher query: 
    {cypher_query}
    Retrieved Context: 
    {retrieved_context}

    ### Example 1: 
    Q: What methods does AromaticSubstructure have?
    Cypher query: MATCH (c:Class {{name: 'AromaticSubstructure'}})-[:HAS]->(f:Function) RETURN f.name, f.comment
    [['f.name', 'f.comment'], ['__init__', 'Constructs an empty <tt>AromaticSubstructure</tt> instance.'], ['__init__', 'Construct a <tt>AromaticSubstructure</tt> instance that consists of the aromatic atoms and bonds of the molecular graph <em>molgraph</em>.'], ['perceive', 'Replaces the currently stored atoms and bonds by the set of aromatic atoms and bonds of the molecular graph <em>molgraph</em>.']]
    A: AromaticSubstructure has the following methods:
    - __init__: Constructs an empty <tt>AromaticSubstructure</tt> instance.
    - __init__: Construct a <tt>AromaticSubstructure</tt> instance that consists of the aromatic atoms and bonds of the molecular graph <em>molgraph</em>.
    - perceive: Replaces the currently stored atoms and bonds by the set of aromatic atoms and bonds of the molecular graph <em>molgraph</em>.
    """.format(retrieved_context = retrieved_context, cypher_query = cypher_query) 
           
def initialize_neo4j():
    neo4j_uri = "neo4j+s://4de35fba.databases.neo4j.io"  
    neo4j_user = "neo4j"  
    neo4j_password = "87YkRGzIftmB-QU8CvYcLNzHZeFAZkeEQpwtZTEa4PU"  
    return GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

def get_pipeline_from_model(model):
    tokenizer = AutoTokenizer.from_pretrained(model,
                                            padding_side = "left")

    return pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )

def get_cypher_query(user_prompt, pipe, schema):
    system_prompt_query= generate_cypher_query_prompt(schema)

    cypher_query = generate_answer_code_llama(user_prompt, system_prompt_query, pipe)
    # print("Cypher query: ", cypher_query)
    return cypher_query

def retrieve_context(driver, user_prompt, pipe, schema): 
    cypher_query = get_cypher_query(user_prompt, pipe, schema)

    query_result = read_query(driver, cypher_query)

    # print("Cypher query result: ", query_result)
    return query_result, cypher_query

def question_rag(user_prompt, pipe_cypher, pipe_answer):
    driver = initialize_neo4j()
    schema = """
    Node properties are the following:
    [
        {"labels": "Project", "properties": ["name"]},
        {"labels": "Folder", "properties": ["name"]},
        {"labels": "File", "properties": ["name"]},
        {"labels": "Class", "properties": ["name", "comment", "attributes"]},
        {"labels": "Function", "properties": ["name", "comment", "parameter", "decorators", "returns"]},
        {"labels": "Parameter", "properties": ["name", "comment", "default", "type"]},
        {"labels": "Decorator", "properties": ["name"]}
    ]

    Relationships point from source to target nodes:
    [
        {"relationship": "INCLUDED_IN", "source": "Folder", "target": "Project"},
        {"relationship": "INCLUDED_IN", "source": "File", "target": "Folder"},
        {"relationship": "INHERITS_FROM", "source": "Class", "target": "Class"},
        {"relationship": "HAS", "source": "Class", "target": ["Function", "Class", "Decorator"]},
        {"relationship": "DECLARED_AT", "source": "Class", "target": "File"},
        {"relationship": "HAS", "source": "Function", "target": "Decorator"},
        {"relationship": "HAS", "source": "Function", "target": "Parameter"}
        {"relationship": "DECLARED_AT", "source": "Function", "target": "File"},
        {"relationship": "OF_TYPE", "source": "Parameter", "target": "Class"}
    ]
    """

    try: 
        query_result, cypher_query = retrieve_context(driver, user_prompt, pipe_cypher, schema)
    except: 
        query_result = "Context could not be retrieved"
        cypher_query = "None"
        
    system_prompt_rag = generate_rag_prompt(query_result, cypher_query)

    final_answer = generate_answer_qwen(user_prompt, system_prompt_rag, pipe_answer)

    #print("####################")
    #print("Question: ", user_prompt)
    #print("Answer: ", final_answer )
    return cypher_query, final_answer

def benchmark_rag(pipe_cypher, pipe_answer):
    with open("/data/shared/projects/graphRAG/graphRAG/graphRAG/benchmark_questions.txt", "r") as f: 
        questions = f.readlines()
    
    benchmark = []
    for question in questions:
        cypher_query, final_answer = question_rag(question, pipe_cypher, pipe_answer)
        benchmark.append({"user_prompt": question, "cypher_query": cypher_query, 
                          "final_answer": final_answer})

    with open("/data/shared/projects/graphRAG/graphRAG/graphRAG/benchmark_results.json", "w") as file:
        json.dump(benchmark, file, indent=4)


if __name__ == "__main__":
    model_cypher = "codellama/CodeLlama-13b-Instruct-hf"

    model_answer = "Qwen/Qwen2.5-7B-Instruct"
    
    pipe_cypher = get_pipeline_from_model(model_cypher)

    pipe_answer = get_pipeline_from_model(model_answer)

    benchmark_rag(pipe_cypher, pipe_answer)

