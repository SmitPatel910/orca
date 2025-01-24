import os
import json
import time
import argparse
from tqdm import tqdm
from pathlib import Path
from utils import output_parser
from model import AgentInteraction
from accuracy import calculate_exact_match_accuracy, calculate_control_flow_accuracy, calculate_block_coverage, calculate_prefix_accuracy, calculate_error_block_accuracy, calculate_error_type_accuracy, calculate_symbol_table_accuracy

# Setting up the paths for the dataset and the temporary dataset directory.
script_directory = Path(__file__).resolve()
base_directory = script_directory.parents[2]

# Accuracy Metrics
def calculate_accuracy(pred_block_execution, pred_error_type, pred_is_error, pred_error_block, pred_block_symbol_table, ground_truth_block_execution_trace, ground_truth_exception_info):
    '''Calculate the accuracy metrics for the predicted output.

    This function calculates the accuracy metrics for the predicted output by comparing it with the ground truth.

    Arguments:
        pred_block_execution (list): The predicted execution order of blocks.
        pred_error_type (str): The predicted error type.
        pred_is_error (bool): Indicates whether the prediction is an error.
        pred_error_block (str): The predicted error block.
        pred_block_symbol_table (list): The predicted symbol table.
        ground_truth_block_execution_trace (list): List of dictionaries
            Example:  [{'block': 1, 'state': {'x': 10, 'y': 20}}]
                
        ground_truth_exception_info (str or None): The ground truth exception type if the code is buggy or None if the code is not buggy.
    
    Returns:
        dict: A dictionary containing the accuracy metrics:
            - "EM" (bool or None): Exact match result.
            - "PF" (list or None): Prefix match recall and precision. [recall, precision]
            - "CF" (list or None): Control flow recall and precision. [recall, precision]
            - "BM" (list or None): Block coverage recall and precision. [recall, precision]
            - "ST" (float or None): Symbol table matching result.
            - "EB" (float or None): Error block matching result.
            - "ET" (float or None): Error type matching result.
            - "is_error" (bool): Indicates whether an error occurred.
    '''

    exact_match = None
    prefix_match_recall = None; prefix_match_precision = None
    control_flow_recall = None; control_flow_precision = None
    block_coverage_recall = None; block_coverage_precision = None
    symbol_match = None 
    error_block_match = None; error_type_match = None
    
    if pred_block_execution:
        exact_match = calculate_exact_match_accuracy(pred_block_execution, ground_truth_block_execution_trace)
        control_flow_recall, control_flow_precision  = calculate_control_flow_accuracy(pred_block_execution, ground_truth_block_execution_trace)
        block_coverage_recall, block_coverage_precision = calculate_block_coverage(pred_block_execution, ground_truth_block_execution_trace)
        prefix_match_recall, prefix_match_precision = calculate_prefix_accuracy(pred_block_execution, ground_truth_block_execution_trace)
        symbol_match = calculate_symbol_table_accuracy(pred_block_symbol_table, ground_truth_block_execution_trace)

    if ground_truth_exception_info:
        error_block_match = 0.0
        error_type_match = 0.0
        if pred_error_type != "" and pred_error_block != "":
            error_block_match = calculate_error_block_accuracy(pred_error_block, ground_truth_block_execution_trace)
            error_type_match = calculate_error_type_accuracy(pred_error_type, ground_truth_exception_info)

    accuracy = {
        "EM": exact_match, # Exact Match
        "PF": [prefix_match_recall, prefix_match_precision], # Prefix Match, Recall, Precision
        "CF": [control_flow_recall, control_flow_precision], # Control Flow, Recall, Precision
        "BM": [block_coverage_recall, block_coverage_precision], # Block Coverage, Recall, Precision
        "ST": symbol_match, # Symbol Table Match
        "EB": error_block_match, # Error Block Match
        "ET": error_type_match, # Error Type Match
        "is_error": pred_is_error # Error Flag
    }

    return accuracy
                
def gpt_pipeline(args, input_cfg, ground_truth_block_execution_trace, ground_truth_exception_info, recursive=False, recursive_count=0):
    '''Execute the GPT pipeline for ORCA evaluation. 
       This function interacts with the `AgentInteraction` class to initialize prompts, 
       call the GPT model API, parse its output, and compute accuracy metrics. 
    
    Arguments:
        args (Namespace): Parsed command-line arguments containing optional parameters:
                          - model (str): The GPT model to use.
                          - temperature (float): Temperature for randomness in generation.
                          - seed (int): Random seed for deterministic behavior.
                          - timeout (int): Timeout for the API call in seconds.

        input_cfg (str): CFG in the text format.
        ground_truth_block_execution (list): The ground truth execution order of blocks.
        ground_truth_exception_info (str or None): The ground truth exception type if the code is buggy.
        recursive (bool): Flag to indicate recursive call.
        recursive_count (int): The number of recursive calls made.

    Returns:
        tuple: A tuple containing:
            - accuracy (dict): A dictionary with the accuracy metrics:
                - "EM" (bool or None): Exact match result.
                - "PF" (list or None): Prefix match recall and precision. [recall, precision]
                - "CF" (list or None): Control flow recall and precision. [recall, precision]
                - "BM" (list or None): Block coverage recall and precision. [recall, precision]
                - "ST" (bool or None): Symbol table matching result.
                - "EB" (bool or None): Error block matching result.
                - "ET" (bool or None): Error type matching result.
                - "is_error" (bool): Indicates whether an error occurred.

            - pred (dict): A dictionary containing:
                - "block_execution" (list): The predicted execution order of blocks.
                - "error_type" (str): The predicted error type.
                - "error_block" (str): The predicted error block.
            - pred_time (float): The time taken to make the prediction (in seconds).
            - output (str): The raw output from the GPT model.
    '''
    # Initialize the Agent
    agent = AgentInteraction()
    
    # Initialize the system and user prompts
    system = agent.init_system_prompt()
    user_Template = agent.init_user_prompt()
    
    # apply zero shot
    system = agent.apply_zero_shot(system)
    user = agent.add_testing_snippet(user_Template, input_cfg)

    # Prepare the message
    message = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    
    try:
        # API Call
        if recursive == True:
            # Recursive call with default parameters (temperature, seed, timeout)
            s_time = time.time()
            model = args.model
            output, response = agent.api_call(message, model, temmprature=0.7, seed=50, timeout=150)
            e_time = time.time()
        else:
            s_time = time.time()
            model = args.model; temperature = args.temperature; seed = args.seed; timeout = args.timeout
            output, response = agent.api_call(message, model, temperature, seed, timeout)
            e_time = time.time()

        # Output Parser
        pred_block_execution, [pred_error_type, pred_error_block, pred_is_error], pred_block_symbol_table = output_parser(output, response)

        # If the output parsing fails, retry the API call recursively up to 3 times.
        if pred_block_execution == [] and recursive_count < 3:
            recursive_count += 1
            gpt_pipeline(args, input_cfg, ground_truth_block_execution_trace, ground_truth_exception_info, recursive=True, recursive_count=recursive_count)
        
        accuracy = calculate_accuracy(pred_block_execution, pred_error_type, pred_is_error, pred_error_block, pred_block_symbol_table, ground_truth_block_execution_trace, ground_truth_exception_info)
        
        pred = {
            "block_execution": pred_block_execution,
            "error_type": pred_error_type,
            "error_block": pred_error_block
        }

        return accuracy, pred, e_time - s_time, output
    
    except Exception as e:
        print("Error in GPT Pipeline: ", e)
        return {}, {}, {}, "Output Parser Failed!"

# Process the dataset
def process_dataset(args, dataset):
    '''Process the dataset using the GPT pipeline for ORCA evaluation.

    This function processes the dataset by iterating over each problem and submission,
    extracting the code, exception information, and ground truth execution order.
    It then calls the GPT pipeline to generate predictions and computes the accuracy metrics.

    Arguments:
        args (Namespace): Parsed command-line arguments containing optional parameters.
        dataset (dict): A dictionary containing the dataset with problem IDs and submissions.
    
    Returns:
        dict: A dictionary containing the processed results for each problem and
                submission in the dataset.
    '''
    response_cache = {}
    count = 0
    
    for probID in tqdm(dataset.keys()):
        if dataset[probID] == {}:   continue
        response_cache[probID] = {}
        submissions = {}

        for index, subID in enumerate(dataset[probID].keys()):
            obj = dataset[probID][subID]
            if obj == {}: continue
            submissions[subID] = {}

            # Extracting the data
            input_cfg = obj['input_cfg']
            exception_info = obj['exception_info']
            ground_truth_block_execution_trace = obj['ground_truth_blocks']

            # If the instance is buggy then get the error type
            if exception_info:
                ground_truth_exception_info = exception_info['class']
            else:
                ground_truth_exception_info = exception_info # None

            if count % 50 == 0 or count == 0:
                print(f"Processing Problem: {probID}, Sub: {subID}, Count: {count}")
            count += 1

            accuracy, pred, pred_time, output = gpt_pipeline(args, input_cfg, ground_truth_block_execution_trace, ground_truth_exception_info)
            
            submissions[subID] = {
                "accuracy": accuracy, 
                "pred": pred, 
                "pred_time": pred_time, 
                "gt": ground_truth_block_execution_trace, 
                "output": output
            }

        response_cache[probID] = submissions

    return response_cache

# Load the dataset
def load_dataset(dataset_path):
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    return data

if __name__ == "__main__":
    # Define command-line arguments using argparse
    parser = argparse.ArgumentParser(description="\nRun the GPT pipeline for baseline b1 evaluation.\n")
    parser.add_argument("--temperature", type=float, default=0.7, help="Set the temperature for randomness in response generation (default: 0.7).")
    parser.add_argument("--model", type=str, default="gpt_35_turbo_16k", help="Set the model to use (default: gpt_35_turbo_16k).")
    parser.add_argument("--seed", type=int, default=42, help="Set the random seed for deterministic behavior (default: 42).")
    parser.add_argument("--timeout", type=int, default=120, help="Set the timeout for the API call in seconds (default: 120).")

    # Parse the arguments from the command line
    args = parser.parse_args()

    # Complete and Incomplete Dataset Paths
    complete_dataset_path = base_directory / "dataset" / "fixeval_merged_cfg.json"
    incomplete_dataset_path = base_directory / "dataset" / "fixeval_incom_merged_cfg.json"
    response_save_dir = base_directory / 'output' / 'orca'
    if not os.path.exists(response_save_dir):
        os.makedirs(response_save_dir)
    
    complete_dataset_response_path = response_save_dir / 'output_cfg_merged.json'
    incomplete_dataset_response_path = response_save_dir / 'output_incom_cfg_merged.json'

    # Load the dataset
    print("Loading the dataset...")
    complete_dataset = load_dataset(complete_dataset_path)
    incomplete_dataset = load_dataset(incomplete_dataset_path)

    print("\nProcessing Complete Code Dataset...")
    complete_dataset_response = process_dataset(args, complete_dataset)
    print("Saving the response...")
    with open(complete_dataset_response_path, 'w') as file:
        json.dump(complete_dataset_response, file)

    print("\nProcessing Incomplete Code Dataset...")
    incomplete_dataset_response = process_dataset(args, incomplete_dataset)
    print("Saving the response...")
    with open(incomplete_dataset_response_path, 'w') as file:
        json.dump(incomplete_dataset_response, file)

