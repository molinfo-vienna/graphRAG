import os
import json
import copy
from utils.evaluation_utils import calculate_metrics, print_metrics, print_comparison_dict, compare_result


def testset_evaluation(mode: str, directory: str) -> None:
    # evaluates the different categories of the testset evaluation for either "manual" mode or "automated" for all the files in the directory 
    if mode not in ["manual", "automated"]: 
        raise ValueError("Mode must be one of the following: manual, automated.")
    categories = ["cypher", "context", "answer", "code", "overall"]
    metrics_template = {cat: {"accuracy": [], "precision": [], "recall": [], "f1": [], "counts": []} for cat in categories} # template to store the results in
    metrics_specific = copy.deepcopy(metrics_template)
    metrics_general = copy.deepcopy(metrics_template)

    files = sorted([f for f in os.listdir(directory) if f.endswith('.json')], key=lambda x: int(x.split('_')[2].split('.')[0])) # sort the result files by ending


    if mode == "manual": 
        files = files[:20]
    for file in files:
        file_path = os.path.join(directory, file)
        with open(file_path, "r") as f:
            results = json.load(f)

        # calculate the metrics for the specific and the general questions
        calculate_metrics(results[:17], metrics_specific, categories, mode) 
        calculate_metrics(results[17:], metrics_general, categories, mode)

    print_metrics("SPECIFIC", metrics_specific)
    print_metrics("GENERAL", metrics_general)


def compare_manual_automated(directory: str) -> None: 
    # compares the result of the automated evaluation with that of the manual one for each category
    categories = ["cypher", "context", "answer", "code", "overall"]
    # the manual evaluation is the 'ground truth' and the dict will show how often a score has been correctly classified/missclassified as something else
    comparison_template = {cat: {"tp": {"tp": 0, "tn": 0, "fp": 0, "fn": 0}, "tn": {"tp": 0, "tn": 0, "fp": 0, "fn": 0}, "fp": {"tp": 0, "tn": 0, "fp": 0, "fn": 0}, "fn": {"tp": 0, "tn": 0, "fp": 0, "fn": 0}} for cat in categories}
    comparison_specific = copy.deepcopy(comparison_template)
    comparison_general = copy.deepcopy(comparison_template)

    files = sorted([f for f in os.listdir(directory) if f.endswith('.json')], key=lambda x: int(x.split('_')[2].split('.')[0]))

    for file in files[:20]:
        file_path = os.path.join(directory, file)
        with open(file_path, "r") as f:
            results = json.load(f)

        for q in results[:17]:
            if "score_context_manual:" in q.keys(): 
                q["score_context_manual"] = q["score_context_manual:"] # correct a naming error
            for cat in categories: 
                compare_result(cat, comparison_specific, q[f"score_{cat}_manual"], q[f"score_{cat}_automated"])
        for q in results[17: ]:
            if "score_context_manual:" in q.keys(): 
                q["score_context_manual"] = q["score_context_manual:"]
            for cat in categories: 
                compare_result(cat, comparison_general, q[f"score_{cat}_manual"], q[f"score_{cat}_automated"])

    print("#### SPECIFIC:")
    print_comparison_dict(comparison_specific)
    print("#### GENERAL:")
    print_comparison_dict(comparison_general)




if __name__ == "__main__": 
    directory = "/data/shared/projects/graphRAG/graphRAG/graphRAG/evaluation/benchmark_results"
    # print("######### MANUAL ########")
    # testset_evaluation("manual", directory)
    # print("######### AUTOMATED ########")
    # testset_evaluation("automated", directory)
    compare_manual_automated(directory=directory)
