import json

def write_new_code(var_value_list, code):
    code_lines = code.split('\n')
    modified_code_lines = []
    var_assignments_by_line = {}

    for var_val_info in var_value_list:
        line_number = int(var_val_info['line']) - 1
        if line_number not in var_assignments_by_line:
            var_assignments_by_line[line_number] = []
        var_assignments_by_line[line_number].append(f"{var_val_info['var_name']} = {var_val_info['var_val']}")
            
    for i, line in enumerate(code_lines):
        if i in var_assignments_by_line:
            new_assignments = "; ".join(var_assignments_by_line[i])
            modified_code_lines.append(new_assignments)
        else:
            modified_code_lines.append(line)

    modified_code = '\n'.join(modified_code_lines)
    return modified_code

with open('../../dataset/other/filtered_fixeval_dataset.json', 'r') as file:
    main_data = json.load(file)

with open('../../dataset/trace/fixeval_crash_trace.json', 'r') as file:
    trace_filtered_data = json.load(file)

# new dataset 
new_dataset = {}

count = 0
for problem_id in trace_filtered_data:
    new_dataset[problem_id] = {}
    for submission_id in trace_filtered_data[problem_id]:
        if trace_filtered_data[problem_id][submission_id] == {}: continue
        new_dataset[problem_id][submission_id] = {}
        list_final_values = []  
        execution_order = trace_filtered_data[problem_id][submission_id]["execution_order"]
        code = main_data[problem_id][submission_id]['code']

        # Crash
        final_trace = trace_filtered_data[problem_id][submission_id]["final_trace"]
        exception_info = trace_filtered_data[problem_id][submission_id]["exception_info"]

        variable_lineNo_list = main_data[problem_id][submission_id]['Input variables']
        for var_name_item in variable_lineNo_list:
            var_name = var_name_item[0]
            line_no = var_name_item[1]
            variable_value = None
            for line in final_trace:
                if line['line'] != int(line_no): continue
                var_val_list = line['var_val']
                for var_val in var_val_list:
                    for key in var_val.keys():
                        if key == var_name:
                            variable_value = var_val[key]
                            list_final_values.append({"line" : line_no, "var_name" : var_name, "var_val" : variable_value})
                        continue
                    continue
                continue
            continue
        # Injecting the input values into the code
        new_code = write_new_code(list_final_values, code)
        lines = new_code.strip().split('\n')
        flag = False
        for line in lines:
            if 'input()' in line:
                flag = True
            if 'main()' in line:
                flag = True
    
        if not flag:
            error_message = trace_filtered_data[problem_id][submission_id]['exception_info'][0]['error_message']
            count += 1
            new_dataset[problem_id][submission_id] = {
                "code" : new_code,
                "execution_order" : execution_order,
                "final_trace" : final_trace,
                "exception_info" : {"class": exception_info[0]['exception_class'], "message": error_message},
            }
print(count)
with open('../../dataset/ready_for_cfg/fixeval_crash_dataset.json', 'w') as file:
    json.dump(new_dataset, file)