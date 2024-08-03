import json
from pathlib import Path
from accuracy import calculate_exact_match, calculate_statement_coverage, calculate_prefix_match, calculate_symbol_table_accuracy

# Setting up the paths for the dataset and the temporary dataset directory.
script_directory = Path(__file__).resolve()
base_directory = script_directory.parents[3]

def process_data(complete, dataset, pred_codeExe):
    EM = 0
    COV_R = 0
    COV_P = 0
    PRE_R = 0
    PRE_P = 0
    ST = 0

    buggy_count = 0
    non_buggy_count = 0

    for id in pred_codeExe.keys():

        exception_info = dataset[id]['exception_info']
        if exception_info:
            buggy_count += 1
        else:
            non_buggy_count += 1

        # Get the prediction for the current Index
        pred_symbol_table = pred_codeExe[id]["symbol_table"]
        pred_exe = pred_codeExe[id]['execution_order']
        # Get the ground truth for the current Index
        gt_exe_symbol_table = dataset[id]['final_trace']
        gt_exe = dataset[id]['ground_truth_execution_order']
        
        try:
            exact_match = calculate_exact_match(pred_exe, gt_exe)
            statement_recall, statement_precision = calculate_statement_coverage(pred_exe, gt_exe)
            prefix_recall, prefix_precision = calculate_prefix_match(pred_exe, gt_exe)

            EM += exact_match
            COV_R += statement_recall
            COV_P += statement_precision
            PRE_R += prefix_recall
            PRE_P += prefix_precision

            if complete:
                symbol_table_accuracy = calculate_symbol_table_accuracy(pred_symbol_table, gt_exe_symbol_table)
                ST += symbol_table_accuracy
        except:
            continue

    total = buggy_count + non_buggy_count

    if complete:
        return {
            "Total Instances": len(pred_codeExe),
            "Buggy Instances": buggy_count,
            "Non-Buggy Instances": non_buggy_count,
            "Exact Match": 100 * (EM/total),
            "Prefix Match Recall": 100 * (PRE_R/total),
            "Prefix Match Precision": 100 * (PRE_P/total),
            "Statement Coverage Recall": 100 * (COV_R/total),
            "Statement Coverage Precision": 100 * (COV_P/total),
            "Symbol Table Accuracy": 100 * (ST/total)
        }
    else:
        return {
            "Total Instances": len(pred_codeExe),
            "Buggy Instances": buggy_count,
            "Non-Buggy Instances": non_buggy_count,
            "Exact Match": 100 * (EM/total),
            "Prefix Match Recall": 100 * (PRE_R/total),
            "Prefix Match Precision": 100 * (PRE_P/total),
            "Statement Coverage Recall": 100 * (COV_R/total),
            "Statement Coverage Precision": 100 * (COV_P/total),
        }

def load_dataset(dataset_path):
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)
    return dataset

if __name__ == "__main__":

    # Complete Code Dataset and Prediction
    complete_code_dataset_dir = base_directory / 'dataset' / 'baseline' / 'fixeval_cfg_b0.json'
    complete_code_pred_dir = base_directory / 'output' / 'baseline' / 'b0' / 'codeExe_fixeval.json'
    # Incomplete Code Dataset and Prediction
    incomplete_code_dataset_dir = base_directory / 'dataset' / 'baseline' / 'fixeval_incom_cfg_b0.json'
    incomplete_code_pred_dir = base_directory / 'output' / 'baseline' / 'b0' / 'codeExe_incom_fixeval.json'

    # Complete Code dataset and Prediction
    complete_dataset = load_dataset(complete_code_dataset_dir)
    pred_complete_codeExe = load_dataset(complete_code_pred_dir)

    # Incomplete Code dataset and Prediction
    incomplete_dataset = load_dataset(incomplete_code_dataset_dir)
    pred_incom_codeExe = load_dataset(incomplete_code_pred_dir)

    # Get the parsed output for the Complete Code
    results_complete = process_data(True, complete_dataset, pred_complete_codeExe)
    results_incomplete = process_data(False, incomplete_dataset, pred_incom_codeExe)

    print("\n===================== RQ3 & RQ4: Complete Code Results =====================")
    for key, value in results_complete.items():
        print(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")

    print("\n===================== RQ3: Incomplete Code Results =====================")
    for key, value in results_incomplete.items():
        print(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
    print()