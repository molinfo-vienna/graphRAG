import os
os.environ['HF_HOME'] = '/data/local/sschoendorfer'
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from huggingface_hub import hf_hub_download
import json
import re 
from transformers.pipelines.text_generation import TextGenerationPipeline
import numpy as np
from transformers import AutoTokenizer, pipeline
import torch
import copy






def testset_evaluation() -> None:
    directory = "/data/shared/projects/graphRAG/graphRAG/graphRAG/benchmark_results"

    categories = ["cypher", "context", "answer", "code", "overall"]
    metrics_template = {cat: {"accuracy": [], "precision": [], "recall": [], "f1": [], "counts": []} for cat in categories}
    metrics_specific = {"manual": copy.deepcopy(metrics_template)}
    metrics_general = {"manual": copy.deepcopy(metrics_template)}

    files = sorted([f for f in os.listdir(directory) if f.endswith('.json')], key=lambda x: int(x.split('_')[2].split('.')[0]))

    for file in files[:20]:
        file_path = os.path.join(directory, file)
        with open(file_path, "r") as f:
            results = json.load(f)

        calculate_metrics(results[:17], metrics_specific, categories)
        calculate_metrics(results[17:], metrics_general, categories)

    print_metrics("SPECIFIC", metrics_specific)
    print_metrics("GENERAL", metrics_general)

def calculate_metrics(questions, metrics, categories):
    counts_template = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    counts = {cat: counts_template.copy() for cat in categories}

    for q in questions:
        if "score_context_manual:" in q.keys(): 
            q["score_context_manual"] = q["score_context_manual:"]
        for cat in categories:
            parse_result(q[f"score_{cat}_manual"], counts[cat])

    for cat in categories:
        metrics["manual"][cat]["accuracy"].append(calculate_accuracy(counts[cat]))
        metrics["manual"][cat]["precision"].append(calculate_precision(counts[cat]))
        metrics["manual"][cat]["recall"].append(calculate_recall(counts[cat]))
        metrics["manual"][cat]["f1"].append(calculate_f1_score(counts[cat]))
        metrics["manual"][cat]["counts"].append(get_counts(counts[cat]))

def calculate_accuracy(counts):
    total = counts["tp"] + counts["tn"] + counts["fp"] + counts["fn"]
    return (counts["tp"] + counts["tn"]) / total 

def calculate_precision(counts):
    total = counts["tp"] + counts["fp"]
    return counts["tp"] / total 

def calculate_recall(counts):
    total = counts["tp"] + counts["fn"]
    return counts["tp"] / total 

def calculate_f1_score(counts):
    precision = calculate_precision(counts)
    recall = calculate_recall(counts)
    return (2 * precision * recall) / (precision + recall)

def get_counts(counts):
    return (counts["tp"], counts["tn"], counts["fp"], counts["fn"])

def parse_result(result, counts):
    result_mapping = {1: "tp", 2: "tn", -1: "fp", 0: "fn", -2: "fp"}
    if (key := result_mapping.get(int(result))) is not None:
        counts[key] += 1

def print_metrics(label, metrics):
    print(f"### RESULTS {label} QUESTIONS ###\n")
    for metric in ["accuracy", "precision", "recall", "f1"]:
        print(f"## {metric.capitalize()}: ")
        for cat in metrics["manual"]:
            if cat == "cypher": 
                continue
            print(f"{cat.capitalize()}: ", np.mean(metrics["manual"][cat][metric]))
        print("\n")


def generate_cypher_eval_prompt(cypher, model) -> str:
    return """
    You are a highly intelligent assistant. Your job is to evaluate cypher queries against a model cypher query.
    Ignore any escape sequences but pay attention to the direction of the relationships.
    If the cypher query matches the model exactly, return 1.
    If the cypher query and the model are not the same, return -1.
    If the cypher query is None, return -1.
    
    IMPORTANT: Only answer with a single number (1, -1). Do not add any text, explanations, or comments.

    ### Example 1: 
    Cypher: \n\nMATCH (p:Project {{name: "CDPKit"}})-[:INCLUDED_IN]->(f:Folder) RETURN f.name
    Model: \\n\\nMATCH (f:Folder)-[:INCLUDED_IN]->(p:Project {{name: 'CDPKit'}}) RETURN f.name
    Answer: -1

    ### Example 2:
    Cypher: \n\nMATCH (f:File)-[:INCLUDED_IN]->(fld:Folder {{name: "Base"}}) RETURN f.name
    Model: \\n\\nMATCH (f:File)-[:INCLUDED_IN]->(folder:Folder {{name: 'Base'}}) RETURN f.name
    Answer: 1

    Cypher: {cypher}
    Model: {model}
    """.format(cypher = f"{cypher}", model = f"{model}")

def generate_context_eval_prompt(context, model) -> str:
    return """
    You are a highly intelligent assistant. Your job is to evaluate a retrieved context against a model context.
    Ignore any formatting.
    If the context matches the model return 1.
    If the context is empty except for placeholders or it says that the context could not be retrieved return 0.
    If the context provides info that is not in the model, return -1.
    
    IMPORTANT: Only answer with a single number (1, -1, 0). Do not add any text, explanations, or comments.

    ### Example 1: 
    Context: [['f.name']]
    Model: ['f.name'], ['Chem'], ['Pharm'], ['Base'], ['Biomol'], ['ConFGen'], ['ConfGen'], ['Descr'], ['ForceField'], ['GRAIL'], ['Grid'], ['Math'], ['MolProp'], ['Shape'], ['Util'], ['Vis']
    Answer: 0

    ### Example 2: 
    Context: [['p.name'],['FragmentList']]
    Model: ["p.name"],["FragmentList"]
    Answer: 1
    
    ### Example 3:
    Context: [["p.name","p.type"],["bond",""Chem.Bond""]]
    Model: ['f.returns'], ['{{type: "int", "comment": ""}}']
    Answer: -1
    

    Context: {context}
    Model: {model}
    """.format(context = f"{context}", model = f"{model}")


def generate_answer_eval_prompt(question, answer, context) -> str:
    return """
    You are a highly intelligent assistant. Your job is to evaluate if an answer correclty answers a question based on the retrieved context. Ignore any python code examples in the answer.
    Ignore any formatting.
    If the answer says it correctly cant answer based on the context return 2.
    If the answer says it wrongly cant answer based on the context even tho the answer would be in the context return 0.
    If the answer positively provides the questioned information based on the context return 1. 
    If the answer provides information that is not present in the context, return -1.
    
    IMPORTANT: Only answer with a single number (1, -1, 0, 2). Do not add any text, explanations, or comments.

    ### Example 1: 
    Question: What are the folders included in the CDPKit Project?
    Context: f.name
    Answer: The CDPKit Project includes the following folder:\n\n- [f.name] (The specific name of the folder is not provided in the retrieved context.) \n\nGiven the limited information, we can only state that there is at least one folder included in the CDPKit Project
    Evaluation: 2

    ### Example 2: 
    Question: What class does the class AromaticRingSet inherit from?
    Context: [['p.name'],['FragmentList']]
    Answer: The class AromaticRingSet inherits from FragmentList.
    Score: 1
    
    ### Example 3:
    Question: What class does the class AromaticRingSet inherit from?
    Context: [['p.name'],['FragmentList']]
    Answer: I cannot answer this based on the provided context.
    Score: 0

    ### Example 4:
    Question: How to generate Conformations with the class ConformerGenerator??
    Context: f.name, f.comment
    Answer: To generate conformations using the `ConformerGenerator` class, you can use the method `generateConformations`.
    Score: -1
    

    Question: {question}
    Context: {context}
    Answer: {answer}
    """.format(question = f"{question}", context = f"{context}", answer = f"{answer}")

def generate_code_eval_prompt(answer) -> str:
    return """
    You are a highly intelligent assistant. Your job is to evaluate if the python code provided in a text is syntactically correct. 
    Ignore any formatting.
    If it is correct return 1. 
    If the text does not contain a code example return 2. 
    If the code example is syntactically incorrect or contains a cypher query return -1
    
    IMPORTANT: Only answer with a single number (1, -1, 2). Do not add any text, explanations, or comments.
    
    ### Example 1: 
    Text: The class AromaticRingSet inherits from FragmentList. \n\nPython example:\n```python\n# This is how you might represent the inheritance relationship in Python\nclass AromaticRingSet(FragmentList):\n    pass\n```
    Score: 1

    Text: {answer}
    """.format(answer = f"{answer}")

def generate_overall_eval_prompt(answer, model) -> str:
    return """
    You are a highly intelligent assistant. Your job is to evaluate if an answer matches a model answer.
    Ignore any formatting or python code.
    If the answer and the model both say they cannot answer something, return 2. 
    If the answer and the model match, return 1
    If the answer does not match the model but rather provides wrong information, return -1. 
    If the answer says it cannot answer something, but the model can, return 0.
    
    IMPORTANT: Only answer with a single number (1, -1, 0, 2). Do not add any text, explanations, or comments.

    ### Example 1: 
    Answer: The CDPKit Project includes the following folder:\n\n- [f.name] (The specific name of the folder is not provided in the retrieved context.) \n\nGiven the limited information, we can only state that there is at least one folder included in the CDPKit Project
    Model: The folders included in the CDPKit Project are:\\n- Chem\\n- Pharm\\n- Base\\n- Biomol\\n- ConfGen\\n- Descr\\n- ForceField\\n- GRAIL\\n- Grid\\n- Math\\n- MolProp\\n- Shape\\n- Util\\n- Vi",
    Evaluation: 0

    ### Example 2:
    Answer: The class AromaticRingSet inherits from FragmentList. \n\n```python\n# Example of accessing the inherited class in Python\nclass AromaticRingSetInheritance:\n    def __init__(self):\n        self.inherited_class = \"FragmentList\"\n        \n# Usage\naromatic_ring_set = AromaticRingSetInheritance()\nprint(aromatic_ring_set.inherited_class)\n``` 
    Model: The class AromaticRingSet inherits from FragmentList. 
    Score: 1
    
    ### Example 3:
    Answer: The parameter `feature` of the function `hasHydrophobicity` stands for \"Feature\". There is no additional comment or default value specified for this parameter. Here is how you might use this parameter in a simple example:\n\n```python\n# Assuming there is a way to call hasHydrophobicity with parameters\nresult = hasHydrophobicity(feature=\"some_value\")\n```\n\nIn this example, `\"some_value\"` would be the value passed to the `feature` parameter. However, note that the exact usage and valid values for the `feature` parameter would depend on the implementation of the `hasHydrophobicity` function.
    Model: I cannot tell what it stands for.
    Score: 2

    ### Example 4:
    Answer: To generate conformations using the `ConformerGenerator` class, you can use the method `generateConformations`.
    Model: To generate conformations using ConformerGenerator, you can use the `generate` method. Here's how you can do it: - `generate`: Generates conformations.
    Score: -1
    

    Answer: {answer}
    Model: {model}
    """.format(answer = f"{answer}", model = f"{model}")

def get_pipeline_from_model(model: str):
    # this will generate a TextGenerationPipeline for the given model
    tokenizer = AutoTokenizer.from_pretrained(model)  # loads the tokenizer for the specified model, padding is added to left side of the input sequence
   
    return pipeline(
        "text-generation", # the pipeline will be used for text generation
        model=model, # loads the specified model
        tokenizer=tokenizer,
        torch_dtype=torch.float16, # precision of the pipeline
        trust_remote_code=True, # if the model has any non standard behavior 
        device_map="auto" # automatically maps the model to the hardware that is available (e.g. GPUs)
        )

def generate_answer_falcon(prompt, pipe, **kwargs): 
    full_prompt = [{"role": "user", "content": prompt}]
    
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
    number_match = re.search(r"-?\d+", output)
    if number_match:
        return number_match.group(0)
    else:
        return ""

def testset_scoring_llm():
    model = "tiiuae/Falcon3-10B-Instruct"
    directory = "/data/shared/projects/graphRAG/graphRAG/graphRAG/benchmark_results"
    pipe = get_pipeline_from_model(model)

    for ix, file in enumerate(sorted(os.listdir(directory), key=lambda x: int(x.split('_')[2].split('.')[0]))):
        if ix > 0: 
            break
        if file.endswith('.json'):
            file_path = os.path.join(directory, file)

            with open(file_path, "r") as f: 
                results = json.load(f)

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
                

        


if __name__ == "__main__": 
    testset_scoring_llm()
