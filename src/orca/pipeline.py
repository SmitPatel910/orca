import os
import json
import time
from pathlib import Path
from utils import output_parser
from model import AgentInteraction
from accuracy import calculate_exact_match_accuracy, calculate_control_flow_accuracy, calculate_block_accuracy, calculate_prefix_accuracy, calculate_error_block_accuracy, calculate_error_type_accuracy, calculate_symbol_table_accuracy

# Setting up the paths for the dataset and the temporary dataset directory.
script_directory = Path(__file__).resolve()
base_directory = script_directory.parents[2]

def calculate_accuracy(block_execution, ground_truth_blocks, error_type, error_block, exception_info, block_symbol_table, is_error):
    exact_match = None
    prefix_match_recall = None; prefix_match_precision = None
    control_flow_recall = None; control_flow_precision = None
    block_coverage_recall = None; block_coverage_precision = None
    symbol_match = None 
    error_block_match = None; error_type_match = None
    
    if block_execution:
        exact_match = calculate_exact_match_accuracy(block_execution, ground_truth_blocks)
        control_flow_recall, control_flow_precision  = calculate_control_flow_accuracy(block_execution, ground_truth_blocks)
        block_coverage_recall, block_coverage_precision = calculate_block_accuracy(block_execution, ground_truth_blocks)
        prefix_match_recall, prefix_match_precision = calculate_prefix_accuracy(block_execution, ground_truth_blocks)
        symbol_match = calculate_symbol_table_accuracy(block_symbol_table, ground_truth_blocks)

    if exception_info:
        error_block_match = 0.0
        error_type_match = 0.0
        if error_type != "" and error_block != "":
            error_block_match = calculate_error_block_accuracy(error_block, ground_truth_blocks)
            error_type_match = calculate_error_type_accuracy(error_type, exception_info)

    accuracy = {
        "EM": exact_match, # Exact Match
        "PF": [prefix_match_recall, prefix_match_precision], # Prefix Match, Recall, Precision
        "CF": [control_flow_recall, control_flow_precision], # Control Flow, Recall, Precision
        "BM": [block_coverage_recall, block_coverage_precision], # Block Coverage, Recall, Precision
        "ST": symbol_match, # Symbol Table Match
        "EB": error_block_match, # Error Block Match
        "ET": error_type_match, # Error Type Match
        "is_error": is_error # Error Flag
    }

    return accuracy

def gpt_pipeline(input_cfg, ground_truth_blocks, exception_info, recursive=False, recursive_count=0):
    
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
        s_time = time.time()
        if recursive == True:
            output, response = agent.api_call(message, temmprature=0.7, seed=50)
        else:
            output, response = agent.api_call(message)
        e_time = time.time()
    except Exception as e:
        print("API Call Failed!, Exception: ", exception_info)
        return {}, {}, {}, "API Call Failed!"
    
    try:
        # Output Parser
        block_execution, [error_type, error_block, is_error], block_symbol_table = output_parser(output, response)

        if block_execution == []:
            if recursive_count < 3:
                recursive_count += 1
                gpt_pipeline(id, input_cfg, ground_truth_blocks, exception_info, recursive=True, recursive_count=recursive_count)
        
        accuracy = calculate_accuracy(block_execution, ground_truth_blocks, error_type, error_block, exception_info, block_symbol_table, is_error)
        
        pred = {
            "block_execution": block_execution, 
            "error_type": error_type, 
            "error_block": error_block
        }

        return accuracy, pred, e_time - s_time, output
    
    except Exception as e:
        print("Output Parser Failed!")
        print("Error: ", e)
        return {}, {}, {}, "Output Parser Failed!"

def process_dataset(dataset):
    response_cache = {}
    count = 0
    
    for probID in dataset.keys():
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
            ground_truth_blocks = obj['ground_truth_blocks']

            # if the instance is buggy get the error type
            if exception_info:
                exception_info = exception_info['class']
            else:
                exception_info = exception_info

            if count % 50 == 0 or count == 0:
                print(f"Processing Problem: {probID}, Sub: {subID}, Count: {count}")
            count += 1

            accuracy, pred, pred_time, output = gpt_pipeline(input_cfg, ground_truth_blocks, exception_info)
            submissions[subID] = {
                "accuracy": accuracy, 
                "pred": pred, 
                "pred_time": pred_time, 
                "gt": ground_truth_blocks, 
                "output": output
            }

        response_cache[probID] = submissions

    return response_cache

def load_dataset(dataset_path):
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    return data

if __name__ == "__main__":

    # Complete and Incomplete Dataset Paths
    complete_dataset_path = base_directory / "dataset" / "fixeval_merged_cfg.json"
    incomplete_dataset_path = base_directory / "dataset" / "fixeval_incom_merged_cfg.json"

    # Response Save Path
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
    complete_dataset_response = process_dataset(complete_dataset)
    print("Saving the response...")
    with open(complete_dataset_response_path, 'w') as file:
        json.dump(complete_dataset_response, file)

    print("\nProcessing Incomplete Code Dataset...")
    incomplete_dataset_response = process_dataset(incomplete_dataset)
    print("Saving the response...")
    with open(incomplete_dataset_response_path, 'w') as file:
        json.dump(incomplete_dataset_response, file)

