from transformers.pipelines.text_generation import TextGenerationPipeline

def generate_answer_qwen(user_prompt: str, system_prompt: str, pipe: TextGenerationPipeline, **kwargs: dict) -> str:
    full_prompt = f"System: {system_prompt}\nUser: {user_prompt}\nAssistant:" # combine the system and user prompt into a from that is easily understoof by Qwen
 
    if "max_new_tokens" not in kwargs:
        kwargs["max_new_tokens"] = 512 # Set a default max_new_tokens if not provided

    # generate the answer
    output = pipe(full_prompt,
                  do_sample=True, # enables sampling and a more varied generation
                  top_k=5, # take the top 5 most likely tokens at each generation step
                  top_p=0.9, 
                  temperature = 0.7, # controls randomness of sampling
                  **kwargs
                  )
    
    output = output[0]["generated_text"] # Extract the relevant part of the generated text
    return output.split('Assistant:', 1)[1].strip() # takes only the portion of the text after the "Assistant: "
  

def generate_rag_prompt(retrieved_context: str, cypher_query: str) -> str:
    # takes the cypher query and retrieved context and creates a system prompt
    # positive examples are added as well as clear instructions
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
           

    