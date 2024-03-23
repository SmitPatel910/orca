import os
from output_parser import get_the_execution_order, extract_info_upto_exception, get_info_on_exception
import json
from tqdm import tqdm

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

folder_path = "output/TraceFiles/"

total_count = 0
incorrect = 0

incorrect_prob_dict = {}
correct_prob_dict = {}

for root, dirs, files in tqdm(os.walk(folder_path)):
    problem_id = root.split('/')[-1]
    incorrect_submissions = {}

    for file in files:
        if not file.endswith(".txt"): continue

        total_count += 1
        file_path = os.path.join(root, file)
        submission_id = file_path.split('/')[-1].split('_')[0]

        with open(file_path, 'r') as txt_file:
            content = txt_file.read()
            incorrect_temp = {}
            try:
                execution_order = get_the_execution_order(content)
                extracted_info, is_exception = extract_info_upto_exception(content)
                state_info, exception_info = get_info_on_exception(content)
                final_trace = extracted_info + state_info
                final_trace = remove_duplicate_items(final_trace)
                if execution_order and final_trace and is_exception and exception_info:
                    incorrect_temp = {
                        "execution_order": execution_order,
                        "final_trace": final_trace,
                        "exception_info": exception_info
                    }
                    if incorrect_temp == {}: continue
                    incorrect += 1
                    incorrect_submissions[submission_id] = {}
                    incorrect_submissions[submission_id] = incorrect_temp
            except Exception as e:
                pass

    if incorrect_submissions != {}:
        incorrect_prob_dict[problem_id] = incorrect_submissions

print(total_count, incorrect)

try:
    with open('../../dataset/fixeval_crash_trace.json', 'w') as file:
        json.dump(incorrect_prob_dict, file, indent=4)
except Exception as e:
    print(e)
    print("Error in writing to file")
