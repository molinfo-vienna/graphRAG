import os
os.environ['HF_HOME'] = '/data/local/sschoendorfer'
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from utils import initialize_neo4j, get_kg_schema, get_pipeline_from_model
from retriever import retrieve_context
from generator import generate_rag_prompt, generate_answer_qwen
import json
from transformers.pipelines.text_generation import TextGenerationPipeline

# Base idea from this article: 
# https://medium.com/@silviaonofrei/code-llamas-knowledge-of-neo4j-s-cypher-query-language-54783d2ad421

def question_rag(user_prompt: str, pipe_cypher: TextGenerationPipeline, pipe_answer: TextGenerationPipeline) -> tuple[str, str]:
    # function to pass a user prompt to the Graph RAG system
    driver = initialize_neo4j() # initialize the neo4j driver to communicate with the Knowledge Graph
    schema = get_kg_schema() # get the KG schema 
    try: 
        query_result, cypher_query = retrieve_context(driver, user_prompt, pipe_cypher, schema)
    except Exception as e: 
        print("Exception while retrieving context: ", e)
        query_result = "Context could not be retrieved" # if there is an exception, the query was not functional
        cypher_query = "None" # set it to None to flag for non-runnable queries during benchmarking 
        
    system_prompt_rag = generate_rag_prompt(query_result, cypher_query) # get the final system prompt for the rag

    final_answer = generate_answer_qwen(user_prompt, system_prompt_rag, pipe_answer) # generate the final answer 

    return cypher_query, final_answer

def benchmark_rag(pipe_cypher: TextGenerationPipeline, pipe_answer: TextGenerationPipeline) -> None:
    # function for running the benchmark questions 
    with open("/data/shared/projects/graphRAG/graphRAG/graphRAG/benchmark_questions.txt", "r") as f: 
        questions = f.readlines()
    
    benchmark = []
    for question in questions:
        cypher_query, final_answer = question_rag(question, pipe_cypher, pipe_answer)
        benchmark.append({"user_prompt": question, "cypher_query": cypher_query, 
                          "final_answer": final_answer, "score": ""})

    with open("/data/shared/projects/graphRAG/graphRAG/graphRAG/benchmark_results.json", "w") as file:
        json.dump(benchmark, file, indent=4)

if __name__ == "__main__":
    model_cypher = "codellama/CodeLlama-13b-Instruct-hf"

    model_answer = "Qwen/Qwen2.5-7B-Instruct"

    pipe_cypher = get_pipeline_from_model(model_cypher)
    
    pipe_answer = get_pipeline_from_model(model_answer)

    cypher_query , answer = question_rag("How can I initialize the class AromaticSubstructure?", pipe_cypher, pipe_answer)
    
    print("Cypher: ", cypher_query)
    print("Final Answer: ", answer)

