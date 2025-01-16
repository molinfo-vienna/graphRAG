import os
os.environ['HF_HOME'] = '/data/local/sschoendorfer'
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from huggingface_hub import hf_hub_download
import json
import re 
from transformers.pipelines.text_generation import TextGenerationPipeline
from utils.rag_utils import get_pipeline_from_model
from utils.scoring_utils import generate_answer_eval_prompt, generate_code_eval_prompt, generate_context_eval_prompt, generate_cypher_eval_prompt, generate_overall_eval_prompt


def generate_answer_falcon(prompt: str, pipe: TextGenerationPipeline, **kwargs: dict) -> str:
    # passes the user prompt to Falcon and gets the output score 
    full_prompt = [{"role": "user", "content": prompt}] # format that Falcon handles best
    
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
    
    output = output[0]["generated_text"][1]["content"] # Extract the relevant part of the generated text
    number_match = re.search(r"-?\d+", output) # Extract only the number in case the answer also had an explanation
    if number_match:
        return number_match.group(0)
    else:
        return ""

def testset_scoring_llm() -> None:
    model = "tiiuae/Falcon3-10B-Instruct" #scoring LLM
    directory = "/data/shared/projects/graphRAG/graphRAG/graphRAG/benchmark_results"
    pipe = get_pipeline_from_model(model)

    for ix, file in enumerate(sorted(os.listdir(directory), key=lambda x: int(x.split('_')[2].split('.')[0]))):
        if file.endswith('.json'):
            file_path = os.path.join(directory, file)

            with open(file_path, "r") as f: 
                results = json.load(f)

            # go through all the benchmark files and score the answers
            for q in results: 
                user_prompt = generate_cypher_eval_prompt(q["cypher_query"], q["model_cypher"])
                q["score_cypher_automated"] = generate_answer_falcon(user_prompt, pipe)
                user_prompt = generate_context_eval_prompt(q["retrieved_context"], q["model_context"])
                q["score_context_automated"] = generate_answer_falcon(user_prompt, pipe)
                user_prompt = generate_answer_eval_prompt(q["user_prompt"], q["final_answer"], q["retrieved_context"])
                q["score_answer_automated"] = generate_answer_falcon(user_prompt, pipe)
                user_prompt = generate_code_eval_prompt(q["final_answer"])
                q["score_code_automated"] = generate_answer_falcon(user_prompt, pipe)
                user_prompt = generate_overall_eval_prompt(q["final_answer"], q["model_answer"])
                q["score_overall_automated"] = generate_answer_falcon(user_prompt, pipe)
            
            with open(file_path, "w") as f: 
                json.dump(results, f, indent=4)