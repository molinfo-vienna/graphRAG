import os
os.environ['HF_HOME'] = '/data/local/sschoendorfer'

from huggingface_hub import hf_hub_download
from neo4j import GraphDatabase
from transformers import AutoTokenizer, pipeline
import torch
import pandas as pd

# Try according to this article
# https://medium.com/@silviaonofrei/code-llamas-knowledge-of-neo4j-s-cypher-query-language-54783d2ad421

def read_query(driver, query, params=None):
    with driver.session() as session:
            result = session.run(query, params)
            output = [r.values() for r in result]
            output.insert(0, result.keys())
            return output
    
def generate_answer(user_prompt, system_prompt, pipe, **kwargs):
    full_prompt = "<s>[INST]<<SYS>>\n{system}\n<</SYS>>\n\n{user}[/INST]\n\n".format(system=f"{system_prompt}",
                                                                        user=f'{user_prompt}')

    # The default max length is pretty small, increase the threshold
    if "max_new_tokens" not in kwargs:
        kwargs["max_new_tokens"] = 512

    output = pipe(full_prompt,
                      do_sample=True,
                      top_k=10,
                      top_p=0.95,
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

def get_graph_schema():
    node_properties_query = """
    CALL apoc.meta.data()
    YIELD label, other, elementType, type, property
    WHERE NOT type = "RELATIONSHIP" AND elementType = "node"
    WITH label AS nodeLabels, collect(property) AS properties
    RETURN {labels: nodeLabels, properties: properties} AS output
    """
    node_props = read_query(node_properties_query)

    rel_query = """
    CALL apoc.meta.data()
    YIELD label, other, elementType, type, property
    WHERE type = "RELATIONSHIP" AND elementType = "node"
    RETURN {source: label, relationship: property, target: other} AS output
    """
    rels = read_query(rel_query)
    return schema_text(node_props, rels)

def generate_cypher_query_prompt(schema):
    return """
    You are an experienced graph databases developer. Provide answers in Cypher query language, based on the following graph Neo4j schema. Only answer with the query and nothing else.

    ### The Schema

    {schema}

    ### Examples 
    Q: What attributes does AtomConfiguration have?
    A: MATCH (c:Class {{name: 'AtomConfiguration'}}) RETURN c.attributes

    Q: List all functions declared in the file "Atom_Functions.doc.py".
    A: MATCH (f:Function)-[:DECLARED_AT]->(fi:File {{name: 'Atom_Functions.doc.py'}}) RETURN f.name

    Q: What functions does the DefaultInteractionAnalyzer have? 
    A: MATCH (c:Class {{name: "DefaultInteractionAnalyzer"}})-[:HAS]->(f:Function) RETURN f.name
    """.format(schema = schema) 

def generate_rag_prompt(retrieved_context):
    return """

    You are an intelligent system. Your job is to answer user questions strictly based on the retrieved context 
    from a Neo4j knowledge graph database. 

    Your response should reflect the content of the retrieved context. Do not add any additional information.

    ### Retrieved context:

    {retrieved_context}

    ### Example 1: 
    Q: What attributes does the class AtomConfiguration have? 
    Retrieved Context: [['c.attributes'], ['[{{"name": "UNDEF", "value": "0"}}, 
    {{"name": "NONE", "value": "1"}}, {{"name": "R", "value": "2"}}, {{"name": "S", "value": "4"}}, 
    {{"name": "EITHER", "value": "8"}}, {{"name": "SP", "value": "16"}}, {{"name": "TB", "value": "20"}}, 
    {{"name": "OH", "value": "41"}}]']]
    A: AtomConfiguration has the attributes UNDEF, NONE, R, S, EITHER, SP, TB and OH

    ### Example 2:
    Q: What attributes does the class AtomContainer have? 
    Retrieved Context: [['c.attributes'], ['[{{"name": "numAtoms", "value": {{"callable": "property", "arguments": ["getNumAtoms"]}}}}]']]
    A: AtomContainer has the attribute numAtoms.
    """.format(retrieved_context = retrieved_context) 
           
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

    cypher_query = generate_answer(user_prompt, system_prompt_query, pipe)
    print("Cypher query: ", cypher_query)
    return cypher_query

def retrieve_context(driver, user_prompt, pipe, schema): 
    cypher_query = get_cypher_query(user_prompt, pipe, schema)

    query_result = read_query(driver, cypher_query)

    print("Cypher query result: ", query_result)
    return query_result

def question_rag(user_prompt):
    driver = initialize_neo4j()
    schema = """
    Node properties are the following:
    [
        {"labels": "Project", "properties": ["name"]},
        {"labels": "Folder", "properties": ["name"]},
        {"labels": "File", "properties": ["name"]},
        {"labels": "Class", "properties": ["name", "attributes"]},
        {"labels": "Function", "properties": ["name", "parameter", "decorators", "returns"]},
        {"labels": "Parameter", "properties": ["name", "default", "type"]},
        {"labels": "Decorator", "properties": ["name"]}
    ]

    Relationships point from source to target nodes:
    [
        {"relationship": "INCLUDED_IN", "source": "Folder", "target": "Project"},
        {"relationship": "INCLUDED_IN", "source": "File", "target": "Folder"},
        {"relationship": "INHERITS_FROM", "source": "Class", "target": "Class"},
        {"relationship": "HAS", "source": "Class", "target": ["Function", "Class"]},
        {"relationship": "DECLARED_AT", "source": "Class", "target": "File"},
        {"relationship": "HAS", "source": "Function", "target": "Decorator"},
        {"relationship": "DECLARED_AT", "source": "Function", "target": "File"},
        {"relationship": "OF_TYPE", "source": "Parameter", "target": "Class"}
    ]
    """

    model = "codellama/CodeLlama-13b-Instruct-hf"
    
    pipe = get_pipeline_from_model(model)

    query_result = retrieve_context(driver, user_prompt, pipe, schema)

    system_prompt_rag = generate_rag_prompt(query_result)

    final_answer = generate_answer(user_prompt, system_prompt_rag, pipe)

    print("####################")
    print("Question: ", user_prompt)
    print("Answer: ", final_answer )

if __name__ == "__main__":
    question_rag("What functions does the DefaultInteractionAnalyzer have?")

