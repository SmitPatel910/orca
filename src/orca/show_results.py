"""
show_results.py (RQ1, RQ2, RQ3, RQ4, RQ5):
This script evaluates the accuracy of ORCA predictions by comparing them against ground truth data.

Functionality:
- Loads dataset and model predictions from JSON files.
- Computes various accuracy metrics such as Exact Match, Prefix Match, Statement Coverage, and Symbol Table Accuracy.
- Differentiates between complete and incomplete code execution scenarios.
- Outputs results in a structured table format.

Dependencies:
- Requires JSON dataset and prediction files.
- Uses accuracy calculation functions from `accuracy.py`.

Input Files:
1. Complete Code:
    - Dataset: 'dataset/fixeval_merged_cfg.json'
    - Predictions: 'output/orca/output_cfg_merged.json'

2. Incomplete Code:
    - Dataset: 'dataset/fixeval_incom_merged_cfg.json'
    - Predictions: 'output/orca/output_incom_cfg_merged.json'

Outputs:
- Prints formatted accuracy results for both complete and incomplete code.
"""

import json
from pathlib import Path
from utils import get_statements_from_blocks, get_scope
from accuracy import get_statement_coverage, get_statement_prefix

# Setting up the paths for the dataset and the temporary dataset directory.
script_directory = Path(__file__).resolve()
base_directory = script_directory.parents[2]

def calculate_rq1_2(RQ_no, table_number, dataset, response_cache):
    '''Calculate RQ1 and RQ2
    Args:
        RQ_no (int): RQ number (1 or 2)
        table_number (int): Table number (1 or 3) and (2 or 4)
        dataset (dict): Dataset containing ground truth data.
            Example: { "prob_id": {
                            "sub_id": { "code": str,
                                        "cfg_block_range": dict,
                                        "ground_truth_execution_order": list,
                                        "ground_truth_blocks": list,
                                        "cfg_block_statements": dict,
                                        "cfg_next_block": dict,
                                        "input_cfg": str,
                                        "exception_info": str
                                    },
                                ...
                            },
                        ...
                    }

        response_cache (dict): Predictions made by ORCA.
            Example: { "prob_id": {
                            "sub_id": { "accuracy": {
                                            "EM": int, 
                                            "PF": [float, float], 
                                            "CF": [float, float],
                                            "BM": [float, float],
                                            "ST": float,
                                            "EB": int,
                                            "Is_Error": bool,
                                        },
                                        "pred": {
                                            "block_execution: list, 
                                            "error_block": int
                                        },
                                        "gt": list,
                                        "output": str
                                    },
                                ...
                            },
                        ...
                    }
    '''
    # Buggy and Non-Buggy Count
    buggy_count = 0
    non_buggy_count = 0

    Error_Block = 0
    true_positive = 0
    true_negative = 0
    false_positive = 0
    false_negative = 0

    for probID in response_cache:
        for subID in response_cache[probID]:
            try:
                obj = dataset[probID][subID]
                res_obj = response_cache[probID][subID]
                exception_info = obj['exception_info']
                if exception_info:
                    buggy_count += 1
                else:
                    non_buggy_count += 1

                if res_obj == {}: continue
                if res_obj['accuracy'] == {}: continue

                accuracy = res_obj['accuracy']
                
            except Exception as e:
                continue

            '''## RQ1 and RQ2 ##'''
            # ============ Table 1/3 ============
            # Error Block Match
            if accuracy['EB']:
                Error_Block += accuracy['EB']

            # ============ Table 2/4 ============
            # Error Detection Match
            if exception_info and accuracy['is_error'] == True:
                true_positive += 1
            elif not exception_info and accuracy['is_error'] == False:
                true_negative += 1
            elif not exception_info and accuracy['is_error'] == True:
                false_positive += 1
            elif exception_info and accuracy['is_error'] == False:
                false_negative += 1

    print(f"\n========================================= RQ{RQ_no} =========================================")
    if RQ_no == 1: print(f"Complete Code Results for Table {table_number} and Table {table_number + 1}\n")
    else: print(f"Incomplete Code Results for Table {table_number} and Table {table_number + 1}\n")

    print(f"Total Instances: {buggy_count + non_buggy_count}")
    print("Buggy Instances: ", buggy_count)
    print("Non-Buggy Instances: ", non_buggy_count)
    print(f"\n---- Table {table_number}: BLOCK-LEVEL FAULT LOCALIZATION ----")
    print(f"Error Block Match: {100 * (Error_Block / buggy_count):.2f}%")
    print(f"\n---- Table {table_number + 1}: INSTANCE-LEVEL RUNTIME-ERROR DETECTION ----")
    print("True Positive Count: ", true_positive)
    print("False Positive Count: ", false_positive)
    print("False Negative Count: ", false_negative)
    print("True Negative Count: ", true_negative)
    print(f"\nTrue Positive Rate: {100 * (true_positive / buggy_count):.2f}%")
    print(f"False Positive Rate: {100 * (false_positive / non_buggy_count):.2f}%")
    print(f"False Negative Rate: {100 * (false_negative / buggy_count):.2f}%")
    print(f"True Negative Rate: {100 * (true_negative / non_buggy_count):.2f}%")
    print(f"\nAccuracy: {100 * ((true_positive + true_negative) / (buggy_count + non_buggy_count)):.2f}%\n")

def calculate_rq3(table_1, table_2, is_complete, dataset, response_cache):
    '''Calculate RQ3
    Args:
        table_1 (int): Table number from the paper (5 or 6)
        table_2 (int): Table number from the paper (7)
        is_complete (bool): Flag to differentiate between complete and incomplete code.
        dataset (dict): Dataset containing ground truth data.
            Example: { "prob_id": {
                            "sub_id": { "code": str,
                                        "cfg_block_range": dict,
                                        "ground_truth_execution_order": list,
                                        "ground_truth_blocks": list,
                                        "cfg_block_statements": dict,
                                        "cfg_next_block": dict,
                                        "input_cfg": str,
                                        "exception_info": str
                                    },
                                ...
                            },
                        ...
                    }

        response_cache (dict): Predictions made by ORCA.
            Example: { "prob_id": {
                            "sub_id": { "accuracy": {
                                            "EM": int, 
                                            "PF": [float, float], 
                                            "CF": [float, float],
                                            "BM": [float, float],
                                            "ST": float,
                                            "EB": int,
                                            "Is_Error": bool,
                                        },
                                        "pred": {
                                            "block_execution: list, 
                                            "error_block": int
                                        },
                                        "gt": list,
                                        "output": str
                                    },
                                ...
                            },
                        ...
                    }           
    '''
    # Buggy and Non-Buggy Count
    buggy_count = 0
    non_buggy_count = 0

    Exact_Match_Execution = 0
    Block_Exe_Pre_R = 0
    Block_Exe_Pre_P = 0
    Statement_Exe_Pre_R = 0
    Statement_Exe_Pre_P = 0
    Block_Cov_R = 0
    Block_Cov_P = 0
    Statement_Cov_R = 0
    Statement_Cov_P = 0
    Block_Transition_R = 0
    Block_Transition_P = 0
    
    for probID in response_cache:
        for subID in response_cache[probID]:
            try:
                obj = dataset[probID][subID]
                res_obj = response_cache[probID][subID]

                exception_info = obj['exception_info']
                if exception_info:
                    buggy_count += 1
                else:
                    non_buggy_count += 1

                if res_obj == {}: continue
                if res_obj['accuracy'] == {}: continue

                # Pred and GT
                gt_blocks = res_obj['gt']
                pred_blocks = res_obj['pred']
                accuracy = res_obj['accuracy']
                block_range = obj['cfg_block_range']

                pd_statement, gt_statement = get_statements_from_blocks(block_range, pred_blocks, gt_blocks)
            except:
                continue
            
            '''Exact Match Execution'''
            if accuracy['EM']:  
                Exact_Match_Execution += accuracy['EM']
            
            '''Prefix Match Execution'''
            # Block
            prefix_recall = accuracy['PF'][0]
            prefix_precision = accuracy['PF'][1]
            if prefix_recall and prefix_precision:
                Block_Exe_Pre_R += prefix_recall
                Block_Exe_Pre_P += prefix_precision
            # Statement
            statement_prefix_recall, statement_prefix_precision = get_statement_prefix(pd_statement, gt_statement)
            if statement_prefix_recall and statement_prefix_precision:
                Statement_Exe_Pre_R += statement_prefix_recall
                Statement_Exe_Pre_P += statement_prefix_precision
            
            '''Coverage'''
            # Block
            block_coverage_recall = accuracy['BM'][0]
            block_coverage_precision = accuracy['BM'][1]
            if block_coverage_recall and block_coverage_precision:
                Block_Cov_R += block_coverage_recall
                Block_Cov_P += block_coverage_precision
            # Statement
            statement_cov_recall, statement_cov_precision = get_statement_coverage(pd_statement, gt_statement)
            if statement_cov_recall and statement_cov_precision:
                Statement_Cov_R += statement_cov_recall
                Statement_Cov_P += statement_cov_precision

            '''Block Control Flow Transition'''
            # Block
            control_flow_recall = accuracy['CF'][0]
            control_flow_precision = accuracy['CF'][1]
            if control_flow_recall and control_flow_precision:
                Block_Transition_R += control_flow_recall
                Block_Transition_P += control_flow_precision

    count = buggy_count + non_buggy_count

    print(f"\n========================================= RQ3 =========================================")
    if is_complete: print(f"Complete Code Results for Table {table_1} and Table {table_2}\n")
    else: print(f"Incomplete Code Results for Table {table_1} and Table {table_2}\n")
    print(f"Total Instances: {count}")
    print("Buggy Instances: ", buggy_count)
    print("Non-Buggy Instances: ", non_buggy_count)
    print(f"\n---- Table {table_1}: EXECUTION TRACES AT STATEMENT LEVEL ----")
    print("\nExact Match Execution: ", f"{100 * (Exact_Match_Execution / count):.2f}%")
    print("\nPrefix Match:")
    print(f"Recall: {100 * (Statement_Exe_Pre_R / count):.2f}%")
    print(f"Precision: {100 * (Statement_Exe_Pre_P / count):.2f}%")
    print("\nCoverage Match:")
    print(f"Recall: {100 * (Statement_Cov_R / count):.2f}%")
    print(f"Precision: {100 * (Statement_Cov_P / count):.2f}%\n")

    print(f"\n---- Table {table_2}: EXECUTION TRACES AT BLOCK LEVEL ----")
    print("\nExact Match Execution: ", f"{100 * (Exact_Match_Execution / count):.2f}%")
    print("\nPrefix Match:")
    print(f"Recall: {100 * (Block_Exe_Pre_R / count):.2f}%")
    print(f"Precision: {100 * (Block_Exe_Pre_P / count):.2f}%")
    print("\nCoverage Match:")
    print(f"Recall: {100 * (Block_Cov_R / count):.2f}%")
    print(f"Precision: {100 * (Block_Cov_P / count):.2f}%")
    print("\nBlock Transition Match:")
    print(f"Recall: {100 * (Block_Transition_R / count):.2f}%")
    print(f"Precision: {100 * (Block_Transition_P / count):.2f}%")

def calculate_rq4(table_number, dataset, response_cache):
    '''Calculate RQ4
    Args:
        table_number (int): Table number from the paper (8)
        dataset (dict): Dataset containing ground truth data.
            Example: { "prob_id": {
                            "sub_id": { "code": str,
                                        "cfg_block_range": dict,
                                        "ground_truth_execution_order": list,
                                        "ground_truth_blocks": list,
                                        "cfg_block_statements": dict,
                                        "cfg_next_block": dict,
                                        "input_cfg": str,
                                        "exception_info": str
                                    },
                                ...
                            },
                        ...
                    }

        response_cache (dict): Predictions made by ORCA.
            Example: { "prob_id": {
                            "sub_id": { "accuracy": {
                                            "EM": int, 
                                            "PF": [float, float], 
                                            "CF": [float, float],
                                            "BM": [float, float],
                                            "ST": float,
                                            "EB": int,
                                            "Is_Error": bool,
                                        },
                                        "pred": {
                                            "block_execution: list, 
                                            "error_block": int
                                        },
                                        "gt": list,
                                        "output": str
                                    },
                                ...
                            },
                        ...
                    }           
    '''
    buggy_count = 0
    non_buggy_count = 0
    Symbol_Table = 0

    for probID in response_cache:
        for subID in response_cache[probID]:
            try:
                obj = dataset[probID][subID]
                res_obj = response_cache[probID][subID]

                exception_info = obj['exception_info']
                if exception_info:
                    buggy_count += 1
                else:
                    non_buggy_count += 1

                if res_obj == {}: continue
                if res_obj['accuracy'] == {}: continue

                accuracy = res_obj['accuracy']
                if accuracy['ST']:
                    Symbol_Table += accuracy['ST']
            except:
                continue
            
    count = buggy_count + non_buggy_count
    print(f"\n========================================= RQ4 =========================================")
    print(f"Complete Code Results for Table {table_number}\n")

    print(f"Total Instances: {count}")
    print("Buggy Instances: ", buggy_count)
    print("Non-Buggy Instances: ", non_buggy_count)
    print(f"\n---- Table {table_number}: VARIABLE VALUE ACCURACY ----")
    print("\nVarible Value Accuracy: ", f"{100 * (Symbol_Table / count):.2f}%\n")

def calculate_rq5(table_number, dataset, response_cache):
    '''Calculate RQ5
    
    Args:
        table_number (int): Table number from the paper (9)
    
        dataset (dict): Dataset containing ground truth data.
            Example: { "prob_id": {
                            "sub_id": { "code": str,
                                        "cfg_block_range": dict,
                                        "ground_truth_execution_order": list,
                                        "ground_truth_blocks": list,
                                        "cfg_block_statements": dict,
                                        "cfg_next_block": dict,
                                        "input_cfg": str,
                                        "exception_info": str
                                    },
                                ...
                            },
                        ...
                    }

        response_cache (dict): Predictions made by ORCA.
            Example: { "prob_id": {
                            "sub_id": { "accuracy": {
                                            "EM": int, 
                                            "PF": [float, float], 
                                            "CF": [float, float],
                                            "BM": [float, float],
                                            "ST": float,
                                            "EB": int,
                                            "Is_Error": bool,
                                        },
                                        "pred": {
                                            "block_execution: list, 
                                            "error_block": int
                                        },
                                        "gt": list,
                                        "output": str
                                    },
                                ...
                            },
                        ...
                    }           
    '''
    buggy_count = 0

    type_statements = {
        'for': {"correct": 0, "incorrect": 0, "total": 0},
        'while': {"correct": 0, "incorrect": 0, "total": 0},
        'if': {"correct": 0, "incorrect": 0, "total": 0},
        'simple': {"correct": 0, "incorrect": 0, "total": 0}
    }
    
    for probID in response_cache:
        for subID in response_cache[probID]:
            try:
                obj = dataset[probID][subID]
                res_obj = response_cache[probID][subID]

                exception_info = obj['exception_info']
                if  not exception_info: continue
                
                if res_obj == {}: continue
                if res_obj['accuracy'] == {}: continue
                
                # Error Block Accuracy
                EB = res_obj['accuracy']['EB']
                
                # Fetch data from dataset
                code = obj['code']
                gt_execution = obj['ground_truth_execution_order']
                
                for_loop, while_loop, if_statement, simple_statement = get_scope(code)
                line_number = gt_execution[-1]
                type_statement = ""
                for scope in for_loop:
                    if scope[0] <= line_number <= scope[1]:
                        type_statement = "for"
                        break
                
                for scope in while_loop:
                    if scope[0] <= line_number <= scope[1]:
                        type_statement = "while"
                        break

                for scope in if_statement:
                    if scope[0] <= line_number <= scope[1]:
                        type_statement = "if"
                        break

                for scope in simple_statement:
                    if scope[0] <= line_number <= scope[1]:
                        type_statement = "simple"
                        break
                
                buggy_count += 1

                if EB == 1:
                    type_statements[type_statement]["correct"] += 1
                    type_statements[type_statement]["total"] += 1
                else:
                    type_statements[type_statement]["incorrect"] += 1
                    type_statements[type_statement]["total"] += 1
                
            except:
                continue
            
    for_pre = f"{100 * ((type_statements['for']['correct'] + type_statements['while']['correct']) / (type_statements['for']['total']+ type_statements['while']['total'])):.2f}"
    if_pre = f"{100 * (type_statements['if']['correct'] / type_statements['if']['total']):.2f}"
    simple_pre = f"{100 * (type_statements['simple']['correct'] / type_statements['simple']['total']):.2f}"
    
    print(f"\n========================================= RQ5 =========================================")
    print(f"Complete Code Results for Table {table_number}\n")

    print("Total: ", buggy_count)
    print(f"\n---- Table {table_number}: CRASH LOCATION PROFILING ----")
    print("Error within Simple Statement: ", type_statements['simple']['total'])
    print("Detected Crashes: ", type_statements['simple']['correct'])
    print(f"Accuracy: {simple_pre}%")

    print("\nError within Branch Statement: ", type_statements['if']['total'])
    print("Detected Crashes: ", type_statements['if']['correct'])
    print(f"Accuracy: {if_pre}%")

    print("\nError within Loop Statement: ", type_statements['for']['total'] + type_statements['while']['total'])
    print("Detected Crashes: ", type_statements['for']['correct'] + type_statements['while']['correct'])
    print(f"Accuracy: {for_pre}%")
    
def process_data(complete_dataset, incomplete_dataset, complete_response_cache, incomplete_response_cache):
    '''
        This function processes the output data and shows the accuracy results for the following RQs:

        Args: 
            complete_dataset (dict): Complete dataset
            incomplete_dataset (dict): Incomplete dataset
            complete_response_cache (dict): Complete dataset response
            incomplete_response_cache (dict): Incomplete dataset response

        Note:
            The function calculates the following RQs:
            RQ1: Error Localization and Error Detection for Complete Code (Table 1 and Table 2)
            RQ2: Error Localization and Error Detection for Incomplete Code (Table 3 and Table 4)
            RQ3: Exact Match, Prefix Match, and Statement Coverage for Complete and Incomplete Code (Table 5,6 and Table 7)
            RQ4: Variable Value Accuracy for Complete Code (Table 8)
            RQ5: Crash Location Profiling for Complete Code (Table 9)
    '''
    # Calculate RQ1 (parameters: rq_number, table_number, dataset, response_cache)
    # Table: 1,2,3,4
    calculate_rq1_2(1, 1, complete_dataset, complete_response_cache)

    # Calculate RQ2 (parameters: rq_number, dataset, response_cache)
    # Table: 1,2,3,4
    calculate_rq1_2(2, 3, incomplete_dataset, incomplete_response_cache)

    # Calculate RQ3 (parameters: table1_number, table2_number, is_complete, dataset, response_cache)
    # Table: 5,6,7
    calculate_rq3(5, 7, True, complete_dataset, complete_response_cache)
    calculate_rq3(6, 7, False, incomplete_dataset, incomplete_response_cache)

    # Calculate RQ4 for Complete Code only(parameters: table_number, dataset, response_cache)
    # Table: 8
    calculate_rq4(8, complete_dataset, complete_response_cache)

    # Calculate RQ5 for Complete Code only(parameters: table_number, dataset, response_cache)
    # Table: 9
    calculate_rq5(9, complete_dataset, complete_response_cache)

# Load the dataset
def load_file(dataset_path):
    '''Load the dataset from the given path.
    Args:
        dataset_path (str): Path to the dataset file.
    Returns:
        dict: A dictionary containing the dataset.
    '''
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    return data

# Entry point
if __name__ == "__main__":

    # Complete and Incomplete Dataset Paths
    complete_dataset_path = base_directory / "dataset" / "fixeval_merged_cfg.json"
    incomplete_dataset_path = base_directory / "dataset" / "fixeval_incom_merged_cfg.json"

    # Response path
    response_save_dir = base_directory / 'output' / 'orca'
    complete_dataset_response_path = response_save_dir / 'output_cfg_merged.json'
    incomplete_dataset_response_path = response_save_dir / 'output_incom_cfg_merged.json'

    # Load the datasets
    complete_dataset = load_file(complete_dataset_path)
    incomplete_dataset = load_file(incomplete_dataset_path)

    complete_results = load_file(complete_dataset_response_path)
    incomplete_results = load_file(incomplete_dataset_response_path)
    
    # Process the data
    process_data(complete_dataset, incomplete_dataset, complete_results, incomplete_results)
    print()
