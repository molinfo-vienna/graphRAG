import copy
import numpy as np

def calculate_metrics(questions: dict, metrics: dict, categories: list, mode: str) -> None:
    # calculate all the metrics for the questions 
    counts_template = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    counts = {cat: copy.deepcopy(counts_template) for cat in categories}

    for q in questions:
        if "score_context_manual:" in q.keys(): 
            q["score_context_manual"] = q["score_context_manual:"] # correct naming error
        for cat in categories:
            parse_result(q[f"score_{cat}_{mode}"], counts[cat]) # get the score counts

    for cat in categories:
        # calculate and store the calculated metrics 
        metrics[cat]["accuracy"].append(calculate_accuracy(counts[cat]))
        metrics[cat]["precision"].append(calculate_precision(counts[cat]))
        metrics[cat]["recall"].append(calculate_recall(counts[cat]))
        metrics[cat]["f1"].append(calculate_f1_score(counts[cat]))
        metrics[cat]["counts"].append(get_counts(counts[cat]))

def calculate_accuracy(counts: dict) -> float:
    # returns the accuracy
    total = counts["tp"] + counts["tn"] + counts["fp"] + counts["fn"]
    return (counts["tp"] + counts["tn"]) / total if total > 0 else 0

def calculate_precision(counts: dict) -> float:
    # returns precision
    total = counts["tp"] + counts["fp"]
    return counts["tp"] / total if total > 0 else 0

def calculate_recall(counts: dict) -> float:
    # returns recall
    total = counts["tp"] + counts["fn"]
    return counts["tp"] / total if total > 0 else 0

def calculate_f1_score(counts: dict) -> float:
    # returns f1 score
    precision = calculate_precision(counts)
    recall = calculate_recall(counts)
    return (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

def get_counts(counts: dict) -> tuple:
    # returns a couple with the number of tp, tn, fp, fn
    return (counts["tp"], counts["tn"], counts["fp"], counts["fn"])

def parse_result(result: str, counts: dict) -> None:
    # parses the result int into its meaning (tp, tn, fp, fn) and increases the count by one
    if result == "": 
        return
    result_mapping = {1: "tp", 2: "tn", -1: "fp", 0: "fn", -2: "fp"}
    if (key := result_mapping.get(int(result))) is not None:
        counts[key] += 1

def print_metrics(label: str, metrics: dict) -> None:
    # prints the metrics result in an easily readable format
    print(f"### RESULTS {label} QUESTIONS ###\n")
    for metric in ["accuracy", "precision", "recall", "f1"]:
        print(f"## {metric.capitalize()}: ")
        for cat in metrics:
            # we take the mean of the metric and its sd
            print(f"{cat.capitalize()}: ", np.mean(metrics[cat][metric]), " +- ", np.std(metrics[cat][metric]))
        print("\n")

def print_comparison_dict(comparison_dict: dict) -> None: 
    # prints the comparison results in an easily readable form 
    for category, counts in comparison_dict.items(): 
        print(f"## {category}:")
        for score, values in counts.items(): 
            print(score, ": ", values)
        print("")


def compare_result(category: str, compare_dict: dict, result_manual: str, result_automated: str) -> None: 
    # parses the results of the manual and automated evaluation, adds them to the comparison dict
    if result_automated == "": 
        return
    result_mapping = {1: "tp", 2: "tn", -1: "fp", 0: "fn", -2: "fp"}
    if (key := result_mapping.get(int(result_manual))) is not None:
        if (value := result_mapping.get(int(result_automated))) is not None:
            compare_dict[category][key][value] += 1