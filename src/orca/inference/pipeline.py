import os
import json
import time
import argparse
from tqdm import tqdm
from pathlib import Path
from utils import output_parser, clean_response
from model import AgentInteraction
from generate_cfg import generate_cfg_for_code

def gpt_pipeline(args, input_cfg, recursive=False, recursive_count=0):
    '''Execute the GPT pipeline for ORCA evaluation. 
       This function interacts with the `AgentInteraction` class to initialize prompts, 
       call the GPT model API, parse its output, and compute accuracy metrics. 
    
    Arguments:
        args (Namespace): Parsed command-line arguments containing optional parameters:
        input_cfg (str): CFG in the text format.
        recursive (bool): Flag to indicate recursive call.
        recursive_count (int): The number of recursive calls made.

    Returns:
        tuple: A tuple containing:
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
        pred_block_execution, [pred_error_type, pred_error_block, pred_is_error], pred_block_symbol_table = output_parser(output)

        # If the output parsing fails, retry the API call recursively up to 3 times.
        if pred_block_execution == [] and recursive_count < 3:
            recursive_count += 1
            gpt_pipeline(args, input_cfg, recursive=True, recursive_count=recursive_count)
                
        pred = {
            "block_execution": pred_block_execution,
            "error_type": pred_error_type,
            "error_block": pred_error_block,
            "is_error": pred_is_error,
            "block_symbol_table": pred_block_symbol_table
        }

        return pred, e_time - s_time, output
    
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
    for _id  in tqdm(dataset):        
        response_cache[_id] = {}
        code = dataset[_id]['code']
        
        # Generate CFG for the code
        # Parameters: code, mode = 'dataset'
        cfg_items = generate_cfg_for_code(code, 'dataset')
        if cfg_items == None:
            print(f"CFG generation failed for ID: {_id}")
            continue
        
        cfg_block_statements, cfg_block_range, cfg_block_connection, cfg_text = cfg_items

        if count % 5 == 0 or count == 0:
            print(f"Processing ID: {_id}, Count: {count}")
            count += 1
        
        pred, pred_time, output = gpt_pipeline(args, cfg_text)
        response_cache[_id] = {
            "output": output,
            "pred": pred,
            "pred_time": pred_time,
        }

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
    parser.add_argument("--model", type=str, help="Set the model to use.", required=True)
    parser.add_argument("--seed", type=int, default=42, help="Set the random seed for deterministic behavior (default: 42).")
    parser.add_argument("--timeout", type=int, default=120, help="Set the timeout for the API call in seconds (default: 120).")
    
    parser.add_argument("--input_dir", type=str, default="../../../dataset/dataset.json", help="Set the input directory for loading the dataset (default: dataset).")
    parser.add_argument("--output_dir", type=str, default="../../../output/orca", help="Set the output directory for saving the response (default: output).")
    
    # Parse the arguments from the command line
    args = parser.parse_args()

    dataset_dir =  args.input_dir        
    response_save_dir = args.output_dir

    if not os.path.exists(dataset_dir):
        print(f"Dataset directory {dataset_dir} does not exist.")
        exit()

    # Load the dataset
    print(f"\nLoading the dataset from {dataset_dir}...")
    dataset = load_dataset(dataset_dir)
    
    print("\nRunning the ORCA for the dataset...")
    response = process_dataset(args, dataset)

    os.makedirs(response_save_dir, exist_ok=True)
    file_path = os.path.join(response_save_dir, "output.json")
    print(f"\nSaving the response to {file_path}...")

    # Clean the response object
    response = clean_response(response)

    with open(file_path, 'w') as file:
        json.dump(response, file, indent=4)
    print("\nORCA evaluation completed successfully!\n")

