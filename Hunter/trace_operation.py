import os
from tqdm import tqdm
from Hunter.output_parser import get_the_execution_order, extract_info_upto_exception, get_info_on_exception

def remove_duplicate_items(extracted_info):
    new_list = []
    for each_dict in extracted_info:
        new_dict = {}
        line_number = each_dict['line']
        if not line_number:
            continue
        var_value_list = each_dict['var_val']
        unique_var_val = [dict(t) for t in {tuple(d.items()) for d in var_value_list}]
        if not unique_var_val:
            continue
        new_dict['line'] = line_number
        new_dict['var_val'] = unique_var_val
        new_list.append(new_dict)
    return new_list

def process_file(file_path):
    with open(file_path, 'r') as txt_file:
        content = txt_file.read()
        
    # Get the execution order and extracted info
    execution_order = get_the_execution_order(content)
    extracted_info, is_exception = extract_info_upto_exception(content)
    if not execution_order or not extracted_info: return None, None
    try:
        if is_exception:
            # Get the exception info and state info
            state_info, exception_info = get_info_on_exception(content)
            final_trace = extracted_info + state_info
            final_trace = remove_duplicate_items(final_trace)

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
    
    buggy_trace_dataset = {}
    nonbuggy_trace_dataset = {}

    for root, dirs, files in tqdm(os.walk((folder_path))):
        problem_id = root.split('/')[-1]
        nonbuggy_submissions = {}
        buggy_submissions = {}
        
        for file in files:
            if not file.endswith(".txt"): continue

            file_path = os.path.join(root, file)
            submission_id = file_path.split('/')[-1].split('_')[0]

            buggy_temp, non_buggy_temp = process_file(file_path)
            if buggy_temp == None and non_buggy_temp == None: continue
            if buggy_temp != None:
                buggy_submissions[submission_id] = {}
                buggy_submissions[submission_id] = buggy_temp
            elif non_buggy_temp != None:
                nonbuggy_submissions[submission_id] = {}
                nonbuggy_submissions[submission_id] = non_buggy_temp

        if nonbuggy_submissions:
            nonbuggy_trace_dataset[problem_id] = nonbuggy_submissions
        if buggy_submissions:
            buggy_trace_dataset[problem_id] = buggy_submissions
        
    return buggy_trace_dataset, nonbuggy_trace_dataset

def extract_trace_info(base_path):
    cache_folder_path = base_path / 'output' / 'TraceFiles'
    cache_folder_path = str(cache_folder_path) + '/'
    buggy_dataset, non_buggy_dataset = main(cache_folder_path)

    return buggy_dataset, non_buggy_dataset