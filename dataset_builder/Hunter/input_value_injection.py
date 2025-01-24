def get_new_code(var_value_list, code):
    '''Inject variable assignments into the code based on their values and line numbers.

    This function modifies a given code snippet by inserting variable assignments 
    at specific line numbers, based on the provided list of variable values.

    Args:
        var_value_list (list): A list of dictionaries, each containing:
            - "line" (int): The line number where the variable is assigned.
            - "var_name" (str): The name of the variable.
            - "var_val" (str): The value of the variable.
        code (str): The source code as a string.

    Returns:
        str: The modified code with injected variable assignments.
    '''

    # Split the code into lines
    code_lines = code.split('\n')
    
    # Dictionary to hold new assignments by line number
    var_assignments_by_line = {}

    # Populate the dictionary with variable assignments
    # key: Line Number
    # Value: List of (variable_name, variable_value) tuples
    for var_val_info in var_value_list:
        line_number = int(var_val_info['line']) - 1   # Convert to zero-indexed
        assignment = f"{var_val_info['var_name']} = {var_val_info['var_val']}" # Create the assignment string
        if line_number not in var_assignments_by_line:
            var_assignments_by_line[line_number] = [] # Initialize the list if line not present
        var_assignments_by_line[line_number].append(assignment) # Add the assignment to the line
    

    # Construct the modified code with injected assignments
    modified_code_lines = []
    for index, line in enumerate(code_lines):
        if index in var_assignments_by_line:
            # Add the new assignments for the current line
            new_assignments = "; ".join(var_assignments_by_line[index]) # Combine multiple assignments with ";"
            modified_code_lines.append(new_assignments) # Add assignments before the original line
        else:
            modified_code_lines.append(line) # Add the original line
    
    # Join the modified lines into a single code string
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
    '''Process code by injecting input variable values based on trace data.

    This function takes a code snippet, a list of input variable names with their
    line numbers, and a final trace of variable states. It identifies the final values 
    of input variables and modifies the code to inject these values.

    Args:
        code (str): The source code to be processed.
        variable_lineNo_list (list): A list of tuples where each tuple contains:
            - var_name (str): Name of the variable.
            - line_no (int): Line number where the variable is defined.
        final_trace (list): A list of dictionaries representing variable states at each line.
            Format: [{"line": int, "var_val": [{"var": value}, ...]}, ...]

    Returns:
        str: The modified code with injected input variable values.
    '''

    list_final_values = []
    # Iterate through each Input variable name and its line number
    for var_name_item in variable_lineNo_list:
        var_name, line_no = var_name_item # Extract variable name and line number
        variable_value = None # Initialize the variable value as None

        # Find the variable value in the final trace for the given line number
        for line in final_trace:
            if line['line'] == int(line_no): # Check if the line matches
                for var_val_dict in line['var_val']:
                    if var_name in var_val_dict:  # Check if the variable exists in the trace
                        variable_value = var_val_dict[var_name] # Get the variable value
                        
                        # Add the variable details to the final values list
                        list_final_values.append({
                            "line" : line_no, 
                            "var_name" : var_name, 
                            "var_val" : variable_value
                        })
                        break
                if variable_value is not None:
                    break # Exit the loop if the variable value is found

    # Modify the code by injecting the input variable values
    new_code = get_new_code(list_final_values, code)

    return new_code

def process_dataset(main_dataset, trace_dataset):
    '''Process a dataset by combining code, input variables, and trace execution details.

    This function takes the main dataset and the trace dataset, processes each problem 
    and submission, and creates a new dataset with transformed code, execution order, 
    traces, and exception information.

    Args:
        main_dataset (dict): The original dataset containing:
        trace_dataset (dict): The trace dataset containing:

    Returns:
        dict: A new processed dataset with the processed `code`:
            {
                prob_id: {
                    sub_id: {
                        "code": str, # Transformed code with input values
                        "execution_order": list,    
                        "final_trace": list,        
                        "exception_info": dict or None
                    }
                }
            }
    '''
    new_dataset = {}
    
    # Iterate through each problem ID in the trace dataset
    for prob_id in trace_dataset:
        new_dataset[prob_id] = {} # Initialize problem-level data

        # Iterate through each submission ID in the trace dataset
        for sub_id in trace_dataset[prob_id]:
            if trace_dataset[prob_id][sub_id] == {}: continue # Skip empty submissions

            # Extract the Code and Input Variables from the original Filtered Dataset
            code = main_dataset[prob_id][sub_id]['code']
            variable_lineNo_list = main_dataset[prob_id][sub_id]['Input variables']
            
            # Extract the Execution Order, Final Trace and Exception Info from the Trace Dataset
            execution_order = trace_dataset[prob_id][sub_id]["execution_order"]
            exception_info = trace_dataset[prob_id][sub_id]["exception_info"]

            # Extract the final trace or fallback to extracted info
            try:
                final_trace = trace_dataset[prob_id][sub_id]["final_trace"]
            except:
                final_trace = trace_dataset[prob_id][sub_id]["extracted_info"]

            # Process exception details if present
            if exception_info:
                error_message = trace_dataset[prob_id][sub_id]['exception_info'][0]['error_message']
                exception_info = {"class": exception_info[0]['exception_class'], "message": error_message}
            else:
                exception_info = None
            
            # Transform the code using the final trace and input variables
            new_code = process_instance(code, variable_lineNo_list, final_trace)
            
            # Inspect the transformed code for validity
            flag = inspect_input_lines(new_code)
            if flag: continue # Skip invalid code
            
            new_dataset[prob_id][sub_id] = {}
            new_dataset[prob_id][sub_id] = {
                "code" : new_code,
                "execution_order" : execution_order,
                "final_trace" : final_trace,
                "exception_info" : exception_info
            }

    return new_dataset

# Entry Point
def inject_input_values(filtered_dataset, buggy_dataset, non_buggy_dataset):

    # Process the Buggy Dataset
    buggy_new_dataset = process_dataset(filtered_dataset, buggy_dataset)

    # Process the Non-Buggy Dataset
    non_buggy_new_dataset = process_dataset(filtered_dataset, non_buggy_dataset)

    return buggy_new_dataset, non_buggy_new_dataset