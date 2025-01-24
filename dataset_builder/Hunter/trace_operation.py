import os
from tqdm import tqdm
from Hunter.output_parser import get_the_execution_order, extract_info_upto_exception, get_info_on_exception

def remove_duplicate_items(extracted_info):
    '''Remove duplicate variable-value pairs from the extracted information.

    This function processes a list of extracted information, ensuring that each item 
    contains unique variable-value pairs. It also skips entries with missing line numbers 
    or empty variable-value pairs.

    Args:
        extracted_info (list): A list of dictionaries representing extracted trace information.
    
    Returns:
        list: A processed list with duplicates removed and invalid entries excluded.
    '''
    # Initialize a new list to store processed information
    new_list = []

    # Loop through each dictionary
    for each_dict in extracted_info:
        new_dict = {} # Initialize a new dictionary to store unique variable-value pairs
        line_number = each_dict['line'] # get the line number
        
        # Skip entries with missing line numbers
        if not line_number:
            continue

        # Extract and deduplicate variable-value pairs
        var_value_list = each_dict['var_val']
        # Use a set of tuples to remove duplicates
        unique_var_val = [dict(t) for t in {tuple(d.items()) for d in var_value_list}]
        
        # Skip entries with empty variable-value pairs
        if not unique_var_val:
            continue

        # Add the processed information to the new list
        new_dict['line'] = line_number
        new_dict['var_val'] = unique_var_val
        new_list.append(new_dict)

    return new_list

def process_file(file_path):
    '''Process a trace file to classify it as buggy or non-buggy.

    This function reads a trace file, extracts execution order, state information, 
    and handles exceptions if present. It categorizes the trace as either buggy or 
    non-buggy based on the presence of an exception and returns the structured data.

    Args:
        file_path (str): Path to the trace file.

    Returns:
        tuple: A tuple containing:
            - buggy_temp (dict or None): Information for buggy traces.
            - non_buggy_temp (dict or None): Information for non-buggy traces.
    '''
    
    # Open the trace file and read its content
    with open(file_path, 'r') as txt_file:
        content = txt_file.read()
        
    # Extract execution order and state information
    execution_order = get_the_execution_order(content) # Get the sequence of executed lines
    extracted_info, is_exception = extract_info_upto_exception(content)  # Extract state info and check for exceptions
    
    # If no execution order or extracted information is found, return None
    if not execution_order or not extracted_info: return None, None

    try:
        if is_exception:
            # Get the exception info and state info
            state_info, exception_info = get_info_on_exception(content) # Extract exception info and state info
            final_trace = extracted_info + state_info # Combine state and exception info
            final_trace = remove_duplicate_items(final_trace) # Remove duplicate variable-value pairs

            if not final_trace or not exception_info: return None, None

            buggy_temp = {
                "execution_order": execution_order,
                "final_trace": final_trace,
                "exception_info": exception_info
            }

            if buggy_temp == {}: return None, None

            return buggy_temp, None
        
        else:
            non_buggy_temp = {
                "execution_order": execution_order,
                "extracted_info": extracted_info,
                "exception_info": None
            }

            if non_buggy_temp == {}: return None, None
            
            return None, non_buggy_temp
    except:
        return None, None

def main(folder_path):
    '''Process executed trace files from a folder to categorize them into buggy and non-buggy datasets.

    This function scans through a directory structure, processes trace files, and categorizes
    them into buggy and non-buggy datasets. Each trace file is associated with a problem ID
    and submission ID.

    Args:
        folder_path (str): The path to the folder containing trace files organized by problem IDs.

    Returns:
        tuple: Two dictionaries:
            - buggy_trace_dataset (dict): Contains buggy trace information.
                Format: {problem_id: {submission_id: {execution_order: [], final_trace: [], exception_info: {}}, ...}
            - nonbuggy_trace_dataset (dict): Contains non-buggy trace information.
                Format: {problem_id: {submission_id: {execution_order: [], extracted_info: [], exception_info: None}, ...}
    '''
    # Initialize datasets to store buggy and non-buggy traces
    buggy_trace_dataset = {}
    nonbuggy_trace_dataset = {}

    # Process trace files
    for root, dirs, files in tqdm(os.walk((folder_path))):
        problem_id = root.split('/')[-1]
        nonbuggy_submissions = {}
        buggy_submissions = {}
        
        for file in files:
            if not file.endswith(".txt"): continue # Skip non-text files

            file_path = os.path.join(root, file) # Get the full path of the file
            submission_id = file_path.split('/')[-1].split('_')[0] # Extract submission ID from the file name

            # Process the trace file and categorize it as buggy or non-buggy
            buggy_temp, non_buggy_temp = process_file(file_path)

            # Skip neither buggy nor non-buggy traces
            if buggy_temp == None and non_buggy_temp == None: continue

            # Add the trace information to the respective dataset
            if buggy_temp != None:
                buggy_submissions[submission_id] = {}
                buggy_submissions[submission_id] = buggy_temp
            elif non_buggy_temp != None:
                nonbuggy_submissions[submission_id] = {}
                nonbuggy_submissions[submission_id] = non_buggy_temp

        # Add problem level trace information to the respective dataset
        if nonbuggy_submissions:
            nonbuggy_trace_dataset[problem_id] = nonbuggy_submissions
        if buggy_submissions:
            buggy_trace_dataset[problem_id] = buggy_submissions
        
    return buggy_trace_dataset, nonbuggy_trace_dataset

# Entry point
def extract_trace_info(base_path):
    cache_folder_path = base_path / 'output' / 'TraceFiles'
    cache_folder_path = str(cache_folder_path) + '/'
    buggy_dataset, non_buggy_dataset = main(cache_folder_path)

    return buggy_dataset, non_buggy_dataset