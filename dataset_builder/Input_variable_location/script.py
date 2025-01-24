import json
from tqdm import tqdm
from Input_variable_location.utils import (
    analyze_code,
    remove_comments_and_blank_lines,
    check_code_conditions,
    filter_code_based_on_input_lines
)

from Input_variable_location.variable_locator import main

def filter_original_dataset(base_path, dataset_path):
    '''Filter the original dataset based on specific conditions like loops, method calls, and input variables.

    This function processes the dataset by removing comments, blank lines, and filtering submissions 
    based on certain code analysis conditions. It further filters the dataset based on the input variable 
    locations extracted from the code.

    Args:
        base_path (str): The base directory path where additional resources or files might be located.
        dataset_path (str): The path to the original dataset file (JSON format).

    Returns:
        dict: A filtered dataset that satisfies the specified conditions.
    '''
    with open (dataset_path, 'r') as f:
        dataset = json.load(f)

    filtered_data = {}

    # Filter Dataset based on the loops, method calls, and other conditions
    for prob_id in tqdm(dataset):
        if prob_id not in filtered_data:    filtered_data[prob_id] = {}

        for sub_id in dataset[prob_id]:
            try:
                submission_block = dataset[prob_id][sub_id]
                code = submission_block['code']
                
                # Remove comments and blank lines from the code
                filtered_code = remove_comments_and_blank_lines(code)
                
                # Extract metadata from the submission
                functions_class = submission_block['functions_class']
                functions_standalone = submission_block['functions_standalone']
                verdict = submission_block['verdict']

                # Analyze the code and check filtering conditions
                analyzer = analyze_code(code)
                result = check_code_conditions(analyzer)

                # Add submission to filtered data if it satisfies conditions
                if result:
                    filtered_data[prob_id][sub_id] = {
                        'code': filtered_code, 
                        'functions_class': functions_class, 
                        'functions_standalone': functions_standalone, 
                        'verdict': verdict
                    } 
            except Exception as e:
                pass

    # Extract input variable locations from the filtered data
    variable_locations = main(filtered_data)

    # Further filter the dataset based on input variable locations
    filtered_dataset = filter_code_based_on_input_lines(variable_locations)

    return filtered_dataset

