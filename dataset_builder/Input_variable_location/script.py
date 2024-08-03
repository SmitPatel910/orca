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
                filtered_code = remove_comments_and_blank_lines(code)
                functions_class = submission_block['functions_class']
                functions_standalone = submission_block['functions_standalone']
                verdict = submission_block['verdict']

                analyzer = analyze_code(code)
                result = check_code_conditions(analyzer)

                if result:
                    filtered_data[prob_id][sub_id] = {
                        'code': filtered_code, 
                        'functions_class': functions_class, 
                        'functions_standalone': functions_standalone, 
                        'verdict': verdict
                    } 
            except Exception as e:
                pass

    # Get the Input variables line from the code
    variable_locations = main(filtered_data)
    # Filter the dataset based on the input variables location
    filtered_dataset = filter_code_based_on_input_lines(variable_locations)

    return filtered_dataset

