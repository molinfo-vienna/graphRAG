from utils import run_query
from neo4j import Driver
from transformers.pipelines.text_generation import TextGenerationPipeline


def retrieve_context(driver: Driver, user_prompt: str, pipe: str, schema: str) -> tuple[str, str]: 
    # retrieves the context from the KG
    cypher_query = get_cypher_query(user_prompt, pipe, schema)

    query_result = run_query(driver, cypher_query)
    
    return query_result, cypher_query

def get_cypher_query(user_prompt: str, pipe: TextGenerationPipeline, schema: str) -> str:
    # gets the cypher query
    system_prompt_query= generate_cypher_query_prompt(schema)

    cypher_query = generate_answer_code_llama(user_prompt, system_prompt_query, pipe)
    
    return cypher_query

def generate_cypher_query_prompt(schema: str) -> str:
    # generates the prompt for the generation of the cypher query
    # the prompt includes a clear instruction and positive examples
    return """
    You are experienced with cypher queries. Provide answers in Cypher query language, *strictly* based on the following graph Neo4j schema. Respect the possible direction of relationships and the possible naming of nodes, properties and relationships. DO NOT CREATE NEW NODES OR RELATIONSHIPS. Only answer with the query and nothing else.

    ### The Schema

    {schema}

    ### Examples 
    Q: What methods does AromaticSubstructure have?
    A: MATCH (c:Class {{name: 'AromaticSubstructure'}})-[:HAS]->(f:Function) RETURN f.name, f.comment

    Q: What does the class AtomPredicate do?
    A: MATCH (c:Class {{name: "AtomPredicate"}}) RETURN c.comment
    """.format(schema = schema) 

def generate_answer_code_llama(user_prompt: str, system_prompt: str, pipe: TextGenerationPipeline, **kwargs: dict) -> str:
    # generates the answer from the code llama model
    full_prompt = "<s>[INST]<<SYS>>\n{system}\n<</SYS>>\n\n{user}[/INST]\n\n".format(system=f"{system_prompt}",
                                                                        user=f'{user_prompt}') # format the full prompt in a way that is easily understood by Code LLama 

    if "max_new_tokens" not in kwargs:
        kwargs["max_new_tokens"] = 512 # The default max length is pretty small, increase the threshold
    
    kwargs.setdefault("temperature", 0.7) # controls randomness of sampling 

    output = pipe(full_prompt,
                      do_sample=True, # enables sampling and a more varied generation
                      top_k=5, # take the top 5 most likely tokens at each generation step
                      top_p=0.9,
                      **kwargs)
    
    output = output[0]["generated_text"] # Extract the relevant part of the generated text
    return output.split('<</SYS>>', 1)[1].split("[/INST]")[1] # takes only the relevant part of the answer 
