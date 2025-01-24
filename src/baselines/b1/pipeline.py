import os
import json
import time
import argparse
from tqdm import tqdm
from pathlib import Path
from utils import output_parser
from model import AgentInteraction
from accuracy import calculate_exact_match, calculate_statement_coverage,  calculate_prefix, calculate_error_location, calculate_error_type

# Setting up the paths for the dataset and the temporary dataset directory.
script_directory = Path(__file__).resolve()
base_directory = script_directory.parents[3]

# Accuracy Calculation
def calculate_accuracy(statement_exe, pred_error_type, pred_is_error, ground_truth_execution_order, ground_truth_exception_info):
    '''Calculate various accuracy metrics for statement execution and error prediction.

    This function computes multiple accuracy metrics based on the predictiton. It evaluates:
        - Exact Match (EM): Whether the predicted execution order matches the ground truth exactly.
        - Statement Coverage (COV): Recall and precision
        - Prefix Match (PRE): Recall and precision for the prefix match.
        - Error Location: Whether the predicted error location matches the ground truth.
        - Error Type: Whether the predicted error type matches the ground truth error type.

    Arguments:
        statement_exe (list): The predicted execution order of statements.
        pred_error_type (str): The predicted error type.
        pred_is_error (bool): A flag indicating whether an error occurred during execution.
        ground_truth_execution_order (list): The ground truth execution order of statements.
        ground_truth_exception_info (dict or None): The ground truth exception or error type information.
        
    Returns:
        dict: A dictionary containing the calculated accuracy metrics:
            - "EM" (bool or None): Exact match result.
            - "PRE" (list or None): Prefix match recall and precision as a list [recall, precision].
            - "COV" (list or None): Statement coverage recall and precision as a list [recall, precision].
            - "ErrorLocation" (bool or None): Whether the predicted error location matches the ground truth.
            - "ErrorType" (bool or None): Whether the predicted error type matches the ground truth.
            - "Is_Error" (bool): The `is_error` flag, indicating whether an error was predicted.
    '''
    exact_match = None
    statement_cov_recall = None
    statement_cov_precision = None 
    prefix_match_recall = None
    prefix_match_precision = None
    error_line_match = None
    error_type_match = None

    if statement_exe:
        exact_match = calculate_exact_match(statement_exe, ground_truth_execution_order)
        statement_cov_recall, statement_cov_precision = calculate_statement_coverage(statement_exe, ground_truth_execution_order)
        prefix_match_recall, prefix_match_precision = calculate_prefix(statement_exe, ground_truth_execution_order)
    
    if ground_truth_exception_info:
        error_line_match = calculate_error_location(statement_exe, ground_truth_execution_order)
        if pred_error_type != "" and pred_is_error:
            error_type_match = calculate_error_type(pred_error_type, ground_truth_exception_info)

    accuracy = {
        "EM": exact_match, 
        "PRE": [prefix_match_recall, prefix_match_precision], # Prefix Match Recall and Precision
        "COV": [statement_cov_recall, statement_cov_precision], # Statement Coverage Recall and Precision
        "ErrorLocation": error_line_match, 
        "ErrorType": error_type_match, 
        "Is_Error": pred_is_error
    }

    return accuracy

# GPT Pipeline
def gpt_pipeline(args, is_complete_code, code, ground_truth_execution_order, ground_truth_exception_info):
    '''Execute the GPT pipeline for baseline b1 evaluation.

    This function interacts with the `AgentInteraction` class to initialize prompts, 
    call the GPT model API, parse its output, and compute accuracy metrics. 
    It processes complete or incomplete code samples based on the provided flag and evaluates the 
    predictions against the ground truth execution order and exception information.

    Arguments:
        args (Namespace): Parsed command-line arguments containing optional parameters:
                          - model (str): The GPT model to use.
                          - temperature (float): Temperature for randomness in generation.
                          - seed (int): Random seed for deterministic behavior.
                          - timeout (int): Timeout for the API call in seconds.
        is_complete_code (bool): A flag indicating whether the input is complete or incomplete code.
        code (str): The source code to analyze.
        ground_truth_execution_order (list): The ground truth execution order of statements.
        ground_truth_exception_info (dict or None): The ground truth exception or error type information.

    Returns:
        tuple: A tuple containing:
            - accuracy (dict): A dictionary with the accuracy metrics:
                - "EM" (bool or None): Exact match result.
                - "PRE" (list or None): Prefix match recall and precision. [recall, precision]
                - "COV" (list or None): Statement coverage recall and precision. [recall, precision]
                - "ErrorLocation" (bool or None): Error location matching result.
                - "ErrorType" (bool or None): Error type matching result.
                - "Is_Error" (bool): Indicates whether an error occurred.
            - pred (dict): A dictionary containing:
                - "statement_execution" (str): The predicted execution order of statements.
                - "error_type" (str): The predicted error type.
                - "is_error" (bool): Indicates whether an error occurred during execution.
            - pred_time (float): The time taken to make the prediction (in seconds).
            - output (str): The raw output from the GPT model.
    '''

    # Initialize the Agent
    agent = AgentInteraction()
    
    # Initialize the system and user prompts
    if is_complete_code:
        system = agent.init_system_prompt(True)
        user_Template = agent.init_user_prompt(True)
    else:
        system = agent.init_system_prompt(False)
        user_Template = agent.init_user_prompt(False)
    
    # apply zero shot
    system = agent.apply_zero_shot(system)
    user = agent.add_testing_snippet(user_Template, code)

    # Prepare the message
    message = [{"role": "system", "content": system}, {"role": "user", "content": user}]

    try:
        # API Call
        try:
            s_time = time.time()
            model = args.model; temperature = args.temperature; seed = args.seed; timeout = args.timeout
            output, response = agent.api_call(message, model, temperature, seed, timeout)
            e_time = time.time()
        except:
            s_time = time.time()
            output, response = agent.api_call(message)
            e_time = time.time()

        # Output Parser
        pred_statement_exe, [pred_error_type, pred_is_error] = output_parser(output)

        # Calculate Accuracy
        accuracy = calculate_accuracy(pred_statement_exe, pred_error_type, pred_is_error, ground_truth_execution_order, ground_truth_exception_info)

        pred = {
            "statement_execution": str(pred_statement_exe),
            "error_type": pred_error_type,
            "is_error": pred_is_error
        }
        
        return accuracy, pred, e_time - s_time, output
    
    except Exception as e:
        print("API Call Failed!")
        print("Error: {e}")
        return {}, {}, {}, "API Call Failed!"

# Process the dataset
def process_dataset(args, dataset, is_complete_code):
    '''Process the dataset using the GPT pipeline for baseline b1 evaluation.

    This function processes the dataset by iterating over each problem and submission,
    extracting the code, exception information, and ground truth execution order.
    It then calls the GPT pipeline to generate predictions and computes the accuracy metrics.

    Arguments:
        args (Namespace): Parsed command-line arguments containing optional parameters.
        dataset (dict): A dictionary containing the dataset with problem IDs and submissions.
        is_complete_code (bool): A flag indicating whether the input is complete or incomplete code.
    
    Returns:
        dict: A dictionary containing the processed results for each problem and
                submission in the dataset.
    '''
    baseline_b1 = {}
    count = 0
    
    for probID in tqdm(dataset.keys()):
        if dataset[probID] == {}: continue
        baseline_b1[probID] = {}
        submissions = {}

        for index, subID in enumerate(dataset[probID].keys()):
            obj = dataset[probID][subID]
            if obj == {}: continue
            submissions[subID] = {}

            # Extracting the data
            code = obj['code']
            ground_truth_exception_info = obj['exception_info']
            ground_truth_execution_order = obj['ground_truth_execution_order']
            
            if count % 50 == 0 or count == 0:
                print(f"Processing Problem: {probID}, Sub: {subID}, Count: {count}")
            count += 1

            accuracy, pred, pred_time, output = gpt_pipeline(args, is_complete_code, code, ground_truth_execution_order, ground_truth_exception_info)

            submissions[subID] = {"accuracy": accuracy, "pred": pred, "pred_time": pred_time, "gt": ground_truth_execution_order, "output": output}

        baseline_b1[probID] = submissions
    
    return baseline_b1

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

    # Complete and Incomplete Code Dataset Directory
    complete_code_dataset = base_directory / 'dataset' / 'fixeval_merged_cfg.json'
    incomplete_code_dataset = base_directory / 'dataset' / 'fixeval_incom_merged_cfg.json'
    response_save_dir = base_directory / 'output' / 'baseline' / 'b1'
    if not response_save_dir.exists():
        os.makedirs(response_save_dir)
    
    # Load the dataset
    print("Loading the dataset...")
    complete_code_data = load_dataset(complete_code_dataset)
    incomplete_code_data = load_dataset(incomplete_code_dataset)

    # Process the Complete Code Dataset
    print("Processing Complete Code Dataset...\n")
    complete_b1_res = process_dataset(args, complete_code_data, True)
    complete_code_res_dir = response_save_dir / 'b1_complete_fixeval.json'
    # Save the results
    print("Saving complete code results...")
    with open(complete_code_res_dir, 'w') as file:
        json.dump(complete_b1_res, file)
    
    # Process the Incomplete Code Dataset
    print("\nProcessing Incomplete Code Dataset...\n")
    incomplete_code_res_dir = response_save_dir / 'b1_incomplete_fixeval.json'
    incom_b1_res = process_dataset(args, incomplete_code_data, False)
    # Save the results
    print("Saving incomplete code results...")
    with open(incomplete_code_res_dir, 'w') as file:
        json.dump(incom_b1_res, file)

    print("\nBaseline B1 Pipeline Finished!\n")