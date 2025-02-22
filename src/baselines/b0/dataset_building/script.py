import os
import json
from pathlib import Path

# Setting up the paths for the dataset and the temporary dataset directory.
script_directory = Path(__file__).resolve()
base_directory = script_directory.parents[4]

def flatten_data(data):
    '''Flatten a hierarchical dataset into a single dictionary with concatenated keys.

    This function takes a dataset where the top-level keys represent `prob_ID`, and the 
    second-level keys represent `sub_ID`. The function flattens this structure into a 
    single dictionary with keys in the format `prob_ID_sub_ID` and values as the original 
    second-level dictionaries.

    Dataset format:
        {
            prob_ID: {
                sub_ID: { },
                sub_ID: { }
            },
            prob_ID: {
                sub_ID: { }
            }
        }

    Flattened output format:
        {
            "prob_ID_sub_ID": { },
            "prob_ID_sub_ID": { },
            "prob_ID_sub_ID": { }
        }

    Arguments:
        data (dict): The hierarchical dataset containing `prob_ID` as top-level keys 
                     and `sub_ID` as second-level keys.

    Returns:
        dict: A flattened dictionary where keys are in the format `prob_ID_sub_ID` 
              and values are the metadata dictionaries associated with each `sub_ID`.
    '''
    falttened_data = {}
    for key in data.keys():
        for sub in data[key]:
            falttened_data[f'{key}_{sub}'] = data[key][sub]
    return falttened_data

def load_data(dataset_path):
    with open(dataset_path, 'r') as file:
        data = json.load(file)
    return data

if __name__ == "__main__":
    
    # Complete Dataset and Incomplete Dataset Directory
    com_dataset_directory = base_directory / "dataset"  / "fixeval_merged_cfg.json"
    incom_dataset_directory = base_directory / "dataset" / "fixeval_incom_merged_cfg.json"

    # Execution Trace data for the buggy code and non-buggy code
    buggy_dataset_directory = base_directory / "dataset_builder" / "temp_dataset" / "buggy_dataset_ready_for_cfg.json"
    nonbuggy_dataset_directory = base_directory / "dataset_builder" / "temp_dataset" / "non_buggy_dateset_ready_for_cfg.json"
    
    # Load the data
    print("Loading the data...")
    complete_data = load_data(com_dataset_directory)
    incomplete_data = load_data(incom_dataset_directory)
    buggy_trace_data = load_data(buggy_dataset_directory)
    nonbuggy_trace_data = load_data(nonbuggy_dataset_directory)
    print("Data loaded successfully!")

    # Merge Complete Code Data object with the Trace Data object
    final_complete_data = {}
    for probID in complete_data:
        for subID in complete_data[probID]:
            complete_code_obj = complete_data[probID][subID]
            try:
                try:
                    trace_obj = buggy_trace_data[probID][subID]
                except:
                    trace_obj = nonbuggy_trace_data[probID][subID]
            except:
                continue

            try:
                trace_data = trace_obj['final_trace']
                if probID not in final_complete_data:
                    final_complete_data[probID] = {}
                if subID not in final_complete_data[probID]:
                    final_complete_data[probID][subID] = {}
                    
                final_complete_data[probID][subID] = {
                    **complete_code_obj,
                    'final_trace': trace_data
                }
            except:
                continue    

    # Merge Incomplete Code Data object with the Trace Data object
    final_incomplete_data = {}
    for probID in incomplete_data:

        for subID in incomplete_data[probID]:

            incom_code_obj = incomplete_data[probID][subID]
            try:
                try:
                    trace_obj = buggy_trace_data[probID][subID]
                except:
                    trace_obj = nonbuggy_trace_data[probID][subID]
            except:
                continue
            
            try:
                final_trace = trace_obj['final_trace']
        
                if probID not in final_incomplete_data:
                    final_incomplete_data[probID] = {}
                if subID not in final_incomplete_data[probID]:
                    final_incomplete_data[probID][subID] = {}
                final_incomplete_data[probID][subID] = {
                    **incom_code_obj,
                    'final_trace': final_trace
                }
            except:
                continue
    
    # Flatten the data
    final_complete_data = flatten_data(final_complete_data)
    final_incomplete_data = flatten_data(final_incomplete_data)

    cache_directory = base_directory / "dataset" / "baseline"
    if not cache_directory.exists():
        os.makedirs(cache_directory)
    # Complete CodeExecutor Dataset
    complete_code_executor_directory = base_directory / "dataset" / "baseline" / "fixeval_cfg_b0.json"
    # Incomplete CodeExecutor Dataset
    incomplete_code_executor_directory = base_directory / "dataset" / "baseline" / "fixeval_incom_cfg_b0.json"

    with open(complete_code_executor_directory, 'w') as file:
        json.dump(final_complete_data, file)
    
    with open(incomplete_code_executor_directory, 'w') as file:
        json.dump(final_incomplete_data, file)
    
    print("CodeExecutor (B0) Dataset created successfully!")

