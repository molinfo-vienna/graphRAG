import os
os.environ['HF_HOME'] = os.getenv("MODEL_LOCATION")
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from utils.rag_utils import initialize_neo4j, get_kg_schema, get_pipeline_from_model
from retriever import retrieve_context
from generator import generate_rag_prompt, generate_answer_qwen
import json
import re 
from transformers.pipelines.text_generation import TextGenerationPipeline
import argparse

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

    return cypher_query, query_result, final_answer


def benchmark_rag(pipe_cypher: TextGenerationPipeline, pipe_answer: TextGenerationPipeline) -> None:
    # function for running the benchmark questions 
    with open("/data/shared/projects/graphRAG/graphRAG/graphRAG/benchmark_questions.txt", "r") as f: 
        testset = f.read()

    pattern = r"Q:\s*(.+?)\nQuery:\s*(.+?)\nC:\s*(.+?)\nA:\s*(.+?)(?=\nQ:|\Z)"

    # Find all matches
    matches = re.findall(pattern, testset, re.DOTALL)

    # Parse into a list of dictionaries
    parsed_questions = [
        {"Question": match[0].strip(), "Query": match[1].strip(), "Context": match[2].strip(), "Answer": match[3].strip()}
        for match in matches
    ]

    for i in range(97, 100): 
        benchmark = []
        for question in parsed_questions:
            cypher_query, query_result, final_answer = question_rag(question["Question"], pipe_cypher, pipe_answer)
            benchmark.append({"user_prompt": question["Question"], "cypher_query": cypher_query, 
                              "retrieved_context": query_result, 
                                "final_answer": final_answer,
                                "model_cypher": question["Query"], "model_answer": question["Answer"],
                                "model_context": question["Context"],
                                "score_cypher_automated": "", 
                                "score_context_automated":"",
                                "score_answer_automated": "", 
                                "score_code_automated":"",
                                "score_overall_automated": "", 
                                "score_cypher_manual": "", 
                                "score_context_manual":"",
                                "score_answer_manual": "",
                                "score_code_manual":"", 
                                "score_overall_manual": ""
                                })

        with open(f"/data/shared/projects/graphRAG/graphRAG/graphRAG/benchmark_results/benchmark_results_{i+1}.json", "w") as file:
            json.dump(benchmark, file, indent=4)


if __name__ == "__main__":
    model_cypher = "codellama/CodeLlama-13b-Instruct-hf"

    model_answer = "Qwen/Qwen2.5-7B-Instruct"

    pipe_cypher = get_pipeline_from_model(model_cypher)
    
    pipe_answer = get_pipeline_from_model(model_answer)

    parser = argparse.ArgumentParser(description="CDPKit Graph RAG: Ask a question via command line")

    parser.add_argument(
        "user_query",
        type=str,
        help="The question you want to ask the CDPKit Graph RAG system."
    )

    args = parser.parse_args()

    _, _, answer = question_rag(args.user_query, pipe_cypher, pipe_answer)
    
    print(answer)

    # benchmark_rag(pipe_cypher, pipe_answer)


