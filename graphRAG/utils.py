import os
os.environ['HF_HOME'] = '/data/local/sschoendorfer'
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from huggingface_hub import hf_hub_download
from neo4j import GraphDatabase, Driver
from transformers import AutoTokenizer, pipeline
from transformers.pipelines.text_generation import TextGenerationPipeline
import torch


def get_pipeline_from_model(model: str) -> TextGenerationPipeline:
    # this will generate a TextGenerationPipeline for the given model
    tokenizer = AutoTokenizer.from_pretrained(model,
                                            padding_side = "left")  # loads the tokenizer for the specified model, padding is added to left side of the input sequence
   
    return pipeline(
        "text-generation", # the pipeline will be used for text generation
        model=model, # loads the specified model
        tokenizer=tokenizer,
        torch_dtype=torch.float16, # precision of the pipeline
        trust_remote_code=True, # if the model has any non standard behavior 
        device_map="auto" # automatically maps the model to the hardware that is available (e.g. GPUs)
    )

def get_pipelines(model_cypher: str, model_answer: str) -> tuple[TextGenerationPipeline, TextGenerationPipeline] :
    # gets the two pipelines necessary 
    pipe_cypher = get_pipeline_from_model(model_cypher)

    pipe_answer = get_pipeline_from_model(model_answer)

    return pipe_cypher, pipe_answer  


def initialize_neo4j() -> Driver:
    # initializes the neo4j driver necessary to query the KG
    neo4j_uri = "neo4j+s://4de35fba.databases.neo4j.io"  
    neo4j_user = "neo4j"  
    neo4j_password = "87YkRGzIftmB-QU8CvYcLNzHZeFAZkeEQpwtZTEa4PU"  
    return GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))


def format_system_prompt(system_prompt: str):
    # necessary as the prompt will otherwise be interpeted incorrectly 
    return system_prompt.replace("{", "{{").replace("}", "}}") 


def run_query(driver: Driver, query: str, params: dict|None =None) -> list:
    with driver.session() as session: # starts new session
            result = session.run(query, params) # executes the query
            output = [r.values() for r in result] # turns the query output into a list with only the values of the result dict
            output.insert(0, result.keys()) # inserts the column headers of the query result at the beginning of the output list 
            return output

def get_kg_schema() -> str:
    # provides the schema of the KG, which is the nodes and relationships that exist
    return """
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

if __name__ == "__main__":
     driver = initialize_neo4j()
     print(run_query(driver, "MATCH (f:Folder)-[:INCLUDED_IN]->(p:Project {name: 'CDPKit'}) RETURN f.name "))