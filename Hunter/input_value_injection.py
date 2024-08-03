def get_new_code(var_value_list, code):
    # Split the code into lines
    code_lines = code.split('\n')
    
    # Dictionary to hold new assignments by line number
    var_assignments_by_line = {}

    # key: Line Number
    # Value: List of (variable_name, variable_value) tuples
    for var_val_info in var_value_list:
        line_number = int(var_val_info['line']) - 1
        assignment = f"{var_val_info['var_name']} = {var_val_info['var_val']}"
        if line_number not in var_assignments_by_line:
            var_assignments_by_line[line_number] = []
        var_assignments_by_line[line_number].append(assignment)
    
    # Modify the code by adding new assignments
    modified_code_lines = []
    for index, line in enumerate(code_lines):
        if index in var_assignments_by_line:
            new_assignments = "; ".join(var_assignments_by_line[index])
            modified_code_lines.append(new_assignments)
        else:
            modified_code_lines.append(line)

    modified_code = '\n'.join(modified_code_lines)

    return modified_code

def inspect_input_lines(code):
    lines = code.strip().split('\n')
    flag = False
    for line in lines:
        if 'input()' in line or 'raw_input()' in line or 'sys.stdin.readline()' in line or 'sys.stdin.read()' in line or 'main()' in line:
            flag = True
            break
    return flag

def process_instance(code, variable_lineNo_list, final_trace):
    list_final_values = []

    # Iterate through each Input variable name and its line number
    for var_name_item in variable_lineNo_list:
        var_name, line_no = var_name_item
        variable_value = None

        # For Each Input line, Get the Trace and find the variable value
        for line in final_trace:
            if line['line'] == int(line_no):
                for var_val_dict in line['var_val']:
                    if var_name in var_val_dict:
                        variable_value = var_val_dict[var_name]
                        list_final_values.append({
                            "line" : line_no, 
                            "var_name" : var_name, 
                            "var_val" : variable_value
                        })
                        break
                if variable_value is not None:
                    break

    # Injecting the input values into the code
    new_code = get_new_code(list_final_values, code)
    return new_code

# with open('../../dataset/filtered_fixeval_dataset.json', 'r') as file:
#     main_data = json.load(file)

# with open('../../dataset/fixeval_crash_trace.json', 'r') as file:
#     trace_dataset = json.load(file)

def process_dataset(main_dataset, trace_dataset):
    new_dataset = {}
    for prob_id in trace_dataset:
        new_dataset[prob_id] = {}
        for sub_id in trace_dataset[prob_id]:
            if trace_dataset[prob_id][sub_id] == {}: continue

            # Extract the Code and Input Variables from the original Filtered Dataset
            code = main_dataset[prob_id][sub_id]['code']
            variable_lineNo_list = main_dataset[prob_id][sub_id]['Input variables']
            
            # Extract the Execution Order, Final Trace and Exception Info from the Trace Dataset
            execution_order = trace_dataset[prob_id][sub_id]["execution_order"]
            exception_info = trace_dataset[prob_id][sub_id]["exception_info"]

            try:
                final_trace = trace_dataset[prob_id][sub_id]["final_trace"]
            except:
                final_trace = trace_dataset[prob_id][sub_id]["extracted_info"]

            if exception_info:
                error_message = trace_dataset[prob_id][sub_id]['exception_info'][0]['error_message']
                exception_info = {"class": exception_info[0]['exception_class'], "message": error_message}
            else:
                exception_info = None
            
            new_code = process_instance(code, variable_lineNo_list, final_trace)
            flag = inspect_input_lines(new_code)
            if flag: continue
            
            new_dataset[prob_id][sub_id] = {}
            new_dataset[prob_id][sub_id] = {
                "code" : new_code,
                "execution_order" : execution_order,
                "final_trace" : final_trace,
                "exception_info" : exception_info
            }

    return new_dataset

# with open('../../dataset/fixeval_crash_for_cfg.json', 'w') as file:
#     json.dump(new_dataset, file)

def inject_input_values(filtered_dataset, buggy_dataset, non_buggy_dataset):

    # Process the Buggy Dataset
    buggy_new_dataset = process_dataset(filtered_dataset, buggy_dataset)

    # Process the Non-Buggy Dataset
    non_buggy_new_dataset = process_dataset(filtered_dataset, non_buggy_dataset)

    return buggy_new_dataset, non_buggy_new_dataset