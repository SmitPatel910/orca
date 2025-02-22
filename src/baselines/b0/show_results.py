"""
show_results.py (RQ3 & RQ4):
This script evaluates the accuracy of model-generated (CodeExecutor - B0) execution predictions by comparing them against ground truth data.

Functionality:
- Loads dataset and model predictions from JSON files.
- Computes various accuracy metrics such as Exact Match, Prefix Match, and Statement Coverage.
- Differentiates between complete and incomplete code execution scenarios.
- Outputs results in a structured table format.

Dependencies:
- Requires JSON dataset and prediction files.
- Uses accuracy calculation functions from `accuracy.py`.

Input Files:
1. Complete Code:
    - Dataset: 'dataset/baseline/fixeval_cfg_b0.json'
    - Predictions: 'output/baseline/b0/codeExe_fixeval.json'

2. Incomplete Code:
    - Dataset: 'dataset/baseline/fixeval_incom_cfg_b0.json'
    - Predictions: 'output/baseline/b0/codeExe_incom_fixeval.json'

Outputs:
- Prints formatted accuracy results for both complete and incomplete code.
"""

import json
from pathlib import Path
from accuracy import calculate_exact_match, calculate_statement_coverage, calculate_prefix_match, calculate_symbol_table_accuracy

# Setting up the paths for the dataset and the temporary dataset directory.
script_directory = Path(__file__).resolve()
base_directory = script_directory.parents[3]

def process_data(complete, dataset, predictions):
    ''' Iterate over the predictions to calculate the accuracy metrics.
    Args:
        complete (bool): Flag to indicate if the dataset is complete or incomplete.
        
        dataset (dict): The dataset containing the ground truth.
            Example: { "id":{   "code": str,
                                "cfg_block_range": dict,
                                "ground_truth_execution_order": list,
                                "ground_truth_blocks": list,
                                "cfg_block_statements": dict,
                                "cfg_next_block": dict,
                                "input_cfg": str,
                                "exception_info": str,
                                "final_trace": list
                            },
                        ...
                     }

        predictions (dict): The predictions made by CodeExecutor (B0).
            Example: { "id":{   "symbol_table": dict,
                                "execution_order": list
                            },
                        ...
                     }
    
    Returns:
        dict: A dictionary containing the accuracy metrics.
            {
                "Total Instances": int,
                "Buggy Instances": int,
                "Non-Buggy Instances": int,
                "Exact Match": float,
                "Prefix Match Recall": float,
                "Prefix Match Precision": float,
                "Statement Coverage Recall": float,
                "Statement Coverage Precision": float,
                "Symbol Table Accuracy": float
            }
    '''
    EM = 0 # Exact Match
    COV_R = 0 # Statement Coverage Recall
    COV_P = 0 # Statement Coverage Precision
    PRE_R = 0 # Prefix Match Recall
    PRE_P = 0 # Prefix Match Precision
    ST = 0 # Symbol Table Accuracy

    buggy_count = 0 # Number of buggy instances
    non_buggy_count = 0 # Number of non-buggy instances

    for id in predictions.keys():
        try:
            # check if the instance is buggy or not
            exception_info = dataset[id]['exception_info']
            if exception_info:
                buggy_count += 1
            else:
                non_buggy_count += 1

            # Get the prediction for the current instance
            pred_symbol_table = predictions[id]["symbol_table"]
            pred_exe = predictions[id]['execution_order']

            # Get the ground truth for the current instance
            gt_exe_symbol_table = dataset[id]['final_trace']
            gt_exe = dataset[id]['ground_truth_execution_order']
        
            # Calculate the Exact Match accuracy
            exact_match = calculate_exact_match(pred_exe, gt_exe)
            EM += exact_match

            # Calculate the Statement Coverage accuracy
            statement_recall, statement_precision = calculate_statement_coverage(pred_exe, gt_exe)
            COV_R += statement_recall
            COV_P += statement_precision

            # Calculate the Prefix Match accuracy
            prefix_recall, prefix_precision = calculate_prefix_match(pred_exe, gt_exe)
            PRE_R += prefix_recall
            PRE_P += prefix_precision

            # Only calculate the Symbol Table accuracy for the complete code
            if complete:
                symbol_table_accuracy = calculate_symbol_table_accuracy(pred_symbol_table, gt_exe_symbol_table)
                ST += symbol_table_accuracy
        except:
            continue
    
    # Calculate the total number of instances
    total = buggy_count + non_buggy_count

    # Prepare the results for the complete code dataset
    if complete:
        return {
            "Total Instances": len(predictions),
            "Buggy Instances": buggy_count,
            "Non-Buggy Instances": non_buggy_count,
            "Exact Match": 100 * (EM/total),
            "Prefix Match Recall": 100 * (PRE_R/total),
            "Prefix Match Precision": 100 * (PRE_P/total),
            "Statement Coverage Recall": 100 * (COV_R/total),
            "Statement Coverage Precision": 100 * (COV_P/total),
            "Symbol Table Accuracy": 100 * (ST/total)
        }
    # Prepare the results for the incomplete code dataset
    else:
        return {
            "Total Instances": len(predictions),
            "Buggy Instances": buggy_count,
            "Non-Buggy Instances": non_buggy_count,
            "Exact Match": 100 * (EM/total),
            "Prefix Match Recall": 100 * (PRE_R/total),
            "Prefix Match Precision": 100 * (PRE_P/total),
            "Statement Coverage Recall": 100 * (COV_R/total),
            "Statement Coverage Precision": 100 * (COV_P/total),
        }

# Load the dataset
def load_dataset(dataset_path):
    """
    Load a JSON dataset from the specified file path.

    Args:
        dataset_path (str or Path): Path to the JSON file.

    Returns:
        dict: A dictionary containing the dataset or the response cache.
    """
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)
    return dataset

# Main Function
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