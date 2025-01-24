import re

def get_the_execution_order(text):
    '''Extract the execution order of line numbers from trace file content.

    This function processes the content of a trace file, identifies executed line numbers
    based on a specific pattern (`example.py:<line_number>`), and removes duplicate
    consecutive line numbers from the result.

    Args:
        text (str): The content of the trace file as a string.

    Returns:
        list: A list of unique, consecutive line numbers (zero-indexed) representing 
              the execution order, excluding the first line in the trace.
    '''

    # Pattern to match line numbers 
    line_number_pattern = r"example\.py:(\d+)"
    
    # Split the content into lines and extract line numbers using regex pattern
    lines = text.strip().split('\n')
    execution_order = [
        int(match.group(1)) - 1 
        for line in lines 
        for match in re.finditer(line_number_pattern, line)
    ]
    
    # Remove duplicate consecutive line numbers
    execution_order_no_duplicates = []
    for number in execution_order:
        # Add the line number if it is the first in the list or different from the last added number
        if not execution_order_no_duplicates or (execution_order_no_duplicates and execution_order_no_duplicates[-1] != number):
            execution_order_no_duplicates.append(number)

    # Skip the first line in the execution order (because of the function definition) and return the result
    return execution_order_no_duplicates[1:]

def extract_info_upto_exception(text):
    '''Extract variable values from trace lines up to the first exception.

    This function parses trace file content to extract variable-value mappings for 
    each line, stopping when an "exception" is encountered. It merges variable data 
    for consecutive trace lines with the same line number.

    Args:
        text (str): The content of the trace file as a string.

    Returns:
        tuple: A tuple containing:
            - merged_data (list): A list of dictionaries with line numbers and variable values.
                Format: [{"line": int, "var_val": [{"var": value}, ...]}, ...]
            - flag (bool): A flag indicating whether an exception was encountered in the trace.
    '''

    # Initialize variables
    extracted_data = []
    lines = text.strip().split('\n') # Split the content into lines
    flag = False # Flag to indicate if an exception was encountered
    prev_line = None # Previous line number
    line_number = None # Current line number
    
    # Iterate over each line in the content
    for line in lines:
        # Check if the line contains the word "exception"
        if "exception" in line:
            flag = True
            break
        
        # Extract line number
        line_number_match = re.search(r':(\d+)', line)
        if line_number_match:
            prev_line = line_number
            line_number = int(line_number_match.group(1)) - 1 # Convert to zero-indexed line number

        # Extract variable-value pairs using regex pattern
        var_value_matches = re.findall(r'\[([^[\]]*(?:\[[^[\]]*])*[^[\]]*)\]', line)

        # Skip lines without variable-value pairs
        if not var_value_matches: continue
        
        # Parse and collect variable-value pairs
        var_val = []
        for match in var_value_matches:
            parts = match.split("=>") # Split the variable and value
            if len(parts) == 2:
                variable = parts[0].strip()
                value = parts[1].strip()
                var_val.append({variable: value}) # Add the variable-value pair to the list
        
        # Skip if no variable-value pairs were found
        if var_val == []: continue

        # Add the line number and variable-value pairs to the extracted data
        extracted_data.append({"line": prev_line , "var_val": var_val})
    
    # Merge variable values for consecutive lines with the same line number
    merged_data = []
    if extracted_data:
        previous_entry = extracted_data[0]
        for current_entry in extracted_data[1:]:
            if previous_entry['line'] == current_entry['line']:
                previous_entry['var_val'].extend(current_entry['var_val']) # Merge variable values
            else:
                merged_data.append(previous_entry) # Append the previous entry
                previous_entry = current_entry # Update to the current entry
        merged_data.append(previous_entry) # Append the last entry

    # Return merged data and the exception flag
    return merged_data, flag

def get_info_on_exception(text):
    '''Extract variable state and exception details from trace file content.

    This function processes the content of a trace file to identify the line where 
    an exception occurred, the variables' state at that point, and detailed exception information.

    Args:
        text (str): The content of the trace file as a string.

    Returns:
        tuple:
            - A list of dictionaries with the line number and variables at the exception point.
              Format: [{"line": int, "var_val": [{"variable": value}, ...]}]
            - A list of dictionaries with exception class and error message details.
              Format: [{"exception_class": str, "error_message": str}]
    '''

    # Split the trace file content into individual lines
    lines = text.strip().split('\n')
    
    # Initialize variables to store extracted information
    exception_info = None
    variables = []

    # Pattern to match the exception message
    exception_message_pattern = r"!\s+test_function:\s+\((.*)\)"

    # Iterate over each line in the content
    for i, line in enumerate(lines):
        if not "exception" in line: continue # Skip lines without the word "exception"

        # Extract line number where the exception occurred
        line_number_match = re.search(r':(\d+)', line)
        line_number = line_number_match.group(1) if line_number_match else None

        # Extract variable-value pairs from the current line
        var_value_matches = re.findall(r'\[([^[\]]*(?:\[[^[\]]*])*[^[\]]*)\]', line)
        for match in var_value_matches:
            parts = match.split("=>") # Split the variable and value
            if len(parts) == 2:
                variable = parts[0].strip()
                value = parts[1].strip()
                variables.append({variable: value})  

        # Process additional lines with variable-value pairs
        j = i + 1
        while j < len(lines) and lines[j].strip().startswith("..."):
            var_value_matches = re.findall(r'\[([^[\]]*(?:\[[^[\]]*])*[^[\]]*)\]', lines[j])
            for var_value in var_value_matches:
                parts = var_value.split(" => ")
                if len(parts) == 2:
                    variable, value = parts
                    variables.append({variable: value})
            j += 1
        
        # Extract detailed exception message
        exception_message_match = re.search(exception_message_pattern, lines[j] if j < len(lines) else "")
        if exception_message_match:
            exception_message = exception_message_match.group(1)
            exception_message = exception_message.strip("\"'")
            
            # Extract class and error message from the exception message
            pattern = r"(<class '.*?'>), (TypeError\((?:[^()]|\([^()]*\))*?\))"
            match = re.search(pattern, exception_message)
            if match:
                class_info = match.group(1)  # Extract the exception class
                type_error_message = match.group(2) # Extract the error message
            
            break # Stop processing after the exception is found
    
    # Return the extracted line number, variables, and exception details
    return [{"line" : int(line_number) - 1, "var_val": variables}], [{"exception_class": class_info, "error_message": type_error_message}]
