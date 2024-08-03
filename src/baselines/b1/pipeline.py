import os
import json
import time
from tqdm import tqdm
from pathlib import Path
from utils import output_parser
from model import AgentInteraction
from accuracy import calculate_exact_match, calculate_statement_coverage,  calculate_prefix, calculate_error_location, calculate_error_type

# Setting up the paths for the dataset and the temporary dataset directory.
script_directory = Path(__file__).resolve()
base_directory = script_directory.parents[3]

def calculate_accuracy(statement_exe, ground_truth_execution_order, error_type, exception_info, is_error):
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
    
    if exception_info:
        error_line_match = calculate_error_location(statement_exe, ground_truth_execution_order)

    if error_type != "":
        error_type_match = calculate_error_type(error_type, exception_info)

    accuracy = {
        "EM": exact_match, 
        "PRE": [prefix_match_recall, prefix_match_precision],
        "COV": [statement_cov_recall, statement_cov_precision],
        "ErrorLocation": error_line_match, 
        "ErrorType": error_type_match, 
        "Is_Error": is_error
    }

    return accuracy

def gpt_pipeline(is_complete_code, code, ground_truth_execution_order, exception_info):
    
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
        s_time = time.time()
        output, response = agent.api_call(message)
        e_time = time.time()
        # Output Parser
        statement_exe, [error_type, is_error] = output_parser(output)
        # Calculate Accuracy
        accuracy = calculate_accuracy(statement_exe, ground_truth_execution_order, error_type, exception_info, is_error)
        pred = {
            "statement_execution": str(statement_exe), 
            "error_type": error_type, 
            "is_error": is_error
        }
        
        return accuracy, pred, e_time - s_time, output
    
    except Exception as e:
        print("API Call Failed!")
        print("Error: {e}")
        return {}, {}, {}, "API Call Failed!"
    
def process_dataset(dataset, is_complete_code):
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
            exception_info = obj['exception_info']
            ground_truth_execution_order = obj['ground_truth_execution_order']
            
            if count % 50 == 0 or count == 0:
                print(f"Processing Problem: {probID}, Sub: {subID}, Count: {count}")
            count += 1

            accuracy, pred, pred_time, output = gpt_pipeline(is_complete_code, code, ground_truth_execution_order, exception_info)

            submissions[subID] = {"accuracy": accuracy, "pred": pred, "pred_time": pred_time, "gt": ground_truth_execution_order, "output": output}

        baseline_b1[probID] = submissions
    
    return baseline_b1

def load_dataset(dataset_path):
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    return data

if __name__ == "__main__":
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

    print("Processing Complete Code Dataset...\n")
    complete_b1_res = process_dataset(complete_code_data, True)
    complete_code_res_dir = response_save_dir / 'b1_complete_fixeval.json'
    # Save the results
    print("Saving complete code results...")
    with open(complete_code_res_dir, 'w') as file:
        json.dump(complete_b1_res, file)
    
    print("\nProcessing Incomplete Code Dataset...\n")
    incomplete_code_res_dir = response_save_dir / 'b1_incomplete_fixeval.json'
    incom_b1_res = process_dataset(incomplete_code_data, False)
    # Save the results
    print("Saving incomplete code results...")
    with open(incomplete_code_res_dir, 'w') as file:
        json.dump(incom_b1_res, file)

    print("\nBaseline B1 Pipeline Finished!\n")