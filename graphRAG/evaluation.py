import os
os.environ['HF_HOME'] = '/data/local/sschoendorfer'
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
# from graphRAG import question_rag
# from utils import get_pipeline_from_model
import json
import re 
# from transformers.pipelines.text_generation import TextGenerationPipeline
import numpy as np


# def benchmark_rag(pipe_cypher: TextGenerationPipeline, pipe_answer: TextGenerationPipeline) -> None:
#     # function for running the benchmark questions 
#     with open("/data/shared/projects/graphRAG/graphRAG/graphRAG/benchmark_questions.txt", "r") as f: 
#         testset = f.read()

#     pattern = r"Q:\s*(.+?)\nQuery:\s*(.+?)\nA:\s*(.+?)(?=\nQ:|\Z)"

#     # Find all matches
#     matches = re.findall(pattern, testset, re.DOTALL)

#     # Parse into a list of dictionaries
#     parsed_questions = [
#         {"Question": match[0].strip(), "Query": match[1].strip(), "Answer": match[2].strip()}
#         for match in matches
#     ]

#     for i in range(80, 100): 
#         benchmark = []
#         for question in parsed_questions:
#             cypher_query, final_answer = question_rag(question["Question"], pipe_cypher, pipe_answer)
#             benchmark.append({"user_prompt": question["Question"], "cypher_query": cypher_query, 
#                             "final_answer": final_answer, "score_cypher_automated": "", 
#                             "score_answer_automated": "", "score_cypher_manual": "", 
#                             "score_answer_manual": "",
#                             "score_python_example:":"", 
#                             "model_cypher": question["Query"], "model_answer": question["Answer"] })

#         with open(f"/data/shared/projects/graphRAG/graphRAG/graphRAG/benchmark_results/benchmark_results_{i+1}.json", "w") as file:
#             json.dump(benchmark, file, indent=4)


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



if __name__ == "__main__": 
    model_answer = "Qwen/Qwen2.5-7B-Instruct"
    
    # pipe_answer = get_pipeline_from_model(model_answer)

    testset_evaluation()