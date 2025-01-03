import os
os.environ['HF_HOME'] = '/data/local/sschoendorfer'
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from huggingface_hub import hf_hub_download
import json
import re 
# from transformers.pipelines.text_generation import TextGenerationPipeline
import numpy as np
from transformers import AutoTokenizer, pipeline
import torch


def generate_answer_qwen(user_prompt: str, system_prompt: str, pipe, **kwargs: dict) -> str:
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


def generate_answer_code_llama(system_prompt: str, user_prompt: str, pipe , **kwargs: dict) -> str:
    # generates the answer from the code llama model
    full_prompt = "<s>[INST]<<SYS>>\n{system}\n<</SYS>>\n\n{user}[/INST]\n\n".format(system=f"{system_prompt}",
                                                                        user=f'{user_prompt}') 
    if "max_new_tokens" not in kwargs:
        kwargs["max_new_tokens"] = 512 # The default max length is pretty small, increase the threshold
    
    kwargs.setdefault("temperature", 0.3) # controls randomness of sampling 

    output = pipe(full_prompt,
                      do_sample=True, # enables sampling and a more varied generation
                      top_k=5, # take the top 5 most likely tokens at each generation step
                      top_p=0.9,
                      **kwargs)
    
    output = output[0]["generated_text"] # Extract the relevant part of the generated text
    output = output.split('<</SYS>>', 1)[1].split("[/INST]")[1] # takes only the relevant part of the answer 
    number_match = re.search(r"-?\d+", output)
    if number_match:
        return number_match.group(0)
    else:
        return ''

def generate_cypher_eval_system_prompt() -> str:
    return """
    You are a highly intelligent assistant. Your job is to evaluate cypher queries against a model cypher query.
    Ignore any escape sequences but pay attention to the direction of the relationships.
    If the cypher query matches the model exactly, return 1.
    If the cypher query and the model are not the same, return -1.
    If the cypher query is None, return -2.
    
    IMPORTANT: Only answer with a single number (1, -1, or -2). Do not add any text, explanations, or comments.

    ### Example 1: 
    Cypher: \n\nMATCH (p:Project {{name: "CDPKit"}})-[:INCLUDED_IN]->(f:Folder) RETURN f.name
    Model: \\n\\nMATCH (f:Folder)-[:INCLUDED_IN]->(p:Project {{name: 'CDPKit'}}) RETURN f.name
    Answer: -1

    ### Example 2:
    Cypher: \n\nMATCH (f:File)-[:INCLUDED_IN]->(fld:Folder {{name: "Base"}}) RETURN f.name
    Model: \\n\\nMATCH (f:File)-[:INCLUDED_IN]->(folder:Folder {{name: 'Base'}}) RETURN f.name
    Answer: 1
    """

def generate_cypher_eval_user_prompt(cypher, model): 
    return """
    Cypher: {cypher}
    Model: {model}
    """.format(cypher = f"{cypher}", model = f"{model}")

def get_pipeline_from_model(model: str):
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


def testset_evaluation() -> None: 
    directory = "/data/shared/projects/graphRAG/graphRAG/graphRAG/benchmark_results"

    metrics_specific = {"manual": {"cypher": {"accuracy": [], 
                                                "precision": [], 
                                                "counts": []}, 
                                    "answer": {"accuracy": [], 
                                                "precision": [], 
                                                "counts": []},
                                    "code": {"accuracy": [], 
                                                "precision": [], 
                                                "counts": []}, 
                                    "overall": {"accuracy": [], 
                                                "precision": [], 
                                                "counts": []}}}
    
    metrics_general = {"manual": {"cypher": {"accuracy": [], 
                                                "precision": [], 
                                                "counts": []}, 
                                    "answer": {"accuracy": [], 
                                                "precision": [], 
                                                "counts": []},
                                    "code": {"accuracy": [], 
                                                "precision": [], 
                                                "counts": []}, 
                                    "overall": {"accuracy": [], 
                                                "precision": [], 
                                                "counts": []}}}
    
    
    for ix, file in enumerate(sorted(os.listdir(directory), key=lambda x: int(x.split('_')[2].split('.')[0]))):
        if ix > 19: 
            break
        if file.endswith('.json'):
            file_path = os.path.join(directory, file)

            with open(file_path, "r") as f: 
                results = json.load(f)

            specific_questions = results[:17]
            general_questions = results[17:]

            calculate_metrics(specific_questions, metrics_specific)
            calculate_metrics(general_questions, metrics_general)

    print("### RESULTS SPECIFIC QUESTIONS ###")
    print("\n")
    print("## Accuracy: ")
    print("Cypher: ", np.mean(metrics_specific["manual"]["cypher"]["accuracy"]))
    print("Answer: ", np.mean(metrics_specific["manual"]["answer"]["accuracy"]))
    print("Code: ", np.mean(metrics_specific["manual"]["code"]["accuracy"]))
    print("Overall: ", np.mean(metrics_specific["manual"]["overall"]["accuracy"]))
    print("\n")
    print("## Precision: ")
    print("Cypher: ", np.mean(metrics_specific["manual"]["cypher"]["precision"]))
    print("Answer: ", np.mean(metrics_specific["manual"]["answer"]["precision"]))
    print("Code: ", np.mean(metrics_specific["manual"]["code"]["precision"]))
    print("Overall: ", np.mean(metrics_specific["manual"]["overall"]["precision"]))
    print("\n\n")
    print("### RESULTS GENERAL QUESTIONS ###")
    print("\n")
    print("## Accuracy: ")
    print("Cypher: ", np.mean(metrics_general["manual"]["cypher"]["accuracy"]))
    print("Answer: ", np.mean(metrics_general["manual"]["answer"]["accuracy"]))
    print("Code: ", np.mean(metrics_general["manual"]["code"]["accuracy"]))
    print("Overall: ", np.mean(metrics_general["manual"]["overall"]["accuracy"]))
    print("\n")
    print("## Precision: ")
    print("Cypher: ", np.mean(metrics_general["manual"]["cypher"]["precision"]))
    print("Answer: ", np.mean(metrics_general["manual"]["answer"]["precision"]))
    print("Code: ", np.mean(metrics_general["manual"]["code"]["precision"]))
    print("Overall: ", np.mean(metrics_general["manual"]["overall"]["precision"]))




def calculate_metrics(questions, metrics):
    counts_cypher_manual = {"tp": 0,
                     "tn" : 0, 
                     "fp" : 0,
                     "fn" : 0
                     }
    counts_answer_manual = {"tp": 0,
                     "tn" : 0, 
                     "fp" : 0,
                     "fn" : 0
                     }
    counts_code_manual = {"tp": 0,
                     "tn" : 0, 
                     "fp" : 0,
                     "fn" : 0
                     }
    counts_overall_manual = {"tp": 0,
                     "tn" : 0, 
                     "fp" : 0,
                     "fn" : 0
                     }
    counts_cypher_automatic = {"tp": 0,
                     "tn" : 0, 
                     "fp" : 0,
                     "fn" : 0
                     }
    counts_answer_automatic = {"tp": 0,
                     "tn" : 0, 
                     "fp" : 0,
                     "fn" : 0
                     }
    counts_code_automatic = {"tp": 0,
                     "tn" : 0, 
                     "fp" : 0,
                     "fn" : 0
                     }
    counts_overall_automatic = {"tp": 0,
                     "tn" : 0, 
                     "fp" : 0,
                     "fn" : 0
                     }
    for q in questions: 
        parse_result(q["score_cypher_manual"], counts_cypher_manual)
        parse_result(q["score_answer_manual"], counts_answer_manual)
        parse_result(q["score_python_example:"], counts_code_manual)
        try: 
            parse_result(q["score_rag_overall_manual"], counts_overall_manual)
        except Exception as e: 
            continue

    metrics["manual"]["cypher"]["accuracy"].append(calculate_accuracy(counts_cypher_manual))
    metrics["manual"]["cypher"]["precision"].append(calculate_precision(counts_cypher_manual)) 
    metrics["manual"]["cypher"]["counts"].append(get_counts(counts_cypher_manual)) 
    metrics["manual"]["answer"]["accuracy"].append(calculate_accuracy(counts_answer_manual))
    metrics["manual"]["answer"]["precision"].append(calculate_precision(counts_answer_manual)) 
    metrics["manual"]["answer"]["counts"].append(get_counts(counts_answer_manual)) 
    metrics["manual"]["code"]["accuracy"].append(calculate_accuracy(counts_code_manual))
    metrics["manual"]["code"]["precision"].append(calculate_precision(counts_code_manual)) 
    metrics["manual"]["code"]["counts"].append(get_counts(counts_code_manual)) 
    metrics["manual"]["overall"]["accuracy"].append(calculate_accuracy(counts_overall_manual))
    metrics["manual"]["overall"]["precision"].append(calculate_precision(counts_overall_manual)) 
    metrics["manual"]["overall"]["counts"].append(get_counts(counts_overall_manual)) 
                       
    
    return metrics
    
        

def calculate_accuracy(counts): 
    return ((counts["tp"] + counts["tn"])/(counts["tp"] + counts["tn"] + counts["fp"] + counts["fn"]))           
                
def calculate_precision(counts): 
    return ((counts["tp"])/(counts["tp"] + counts["fp"]))

def get_counts(counts): 
    return (counts["tp"], counts["tn"], counts["fp"], counts["fn"])

def parse_result(result, counts):
    true_positive = 1
    true_negative = 2
    false_positive = -1
    false_negative = 0
    not_runnable = -2

    result = int(result)

    if result == true_positive:
        counts["tp"] += 1
    elif result == true_negative: 
        counts["tn"] += 1
    elif result == false_positive or result == not_runnable: 
        counts["fp"] += 1
    elif result == false_negative: 
        counts["fn"] += 1



def evaluate_cypher():
    model = "codellama/CodeLlama-13b-Instruct-hf"
    directory = "/data/shared/projects/graphRAG/graphRAG/graphRAG/benchmark_results"
    pipe_cypher = get_pipeline_from_model(model)
    system_prompt = generate_cypher_eval_system_prompt()

    for ix, file in enumerate(sorted(os.listdir(directory), key=lambda x: int(x.split('_')[2].split('.')[0]))):
        if ix > 0: 
            break
        if file.endswith('.json'):
            file_path = os.path.join(directory, file)

            with open(file_path, "r") as f: 
                results = json.load(f)

            for q in results: 
                user_prompt = generate_cypher_eval_user_prompt(q["cypher_query"], q["model_cypher"])
                q["score_cypher_automated"] = generate_answer_code_llama(system_prompt=system_prompt, user_prompt=user_prompt, pipe=pipe_cypher).strip("\n")
                print("hello")


            



if __name__ == "__main__": 
    evaluate_cypher()