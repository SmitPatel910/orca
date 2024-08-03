import re

def get_the_execution_order(text):
    line_number_pattern = r"example\.py:(\d+)"
    lines = text.strip().split('\n')
    execution_order = [int(match.group(1))-1 for line in lines for match in re.finditer(line_number_pattern, line)]
    execution_order_no_duplicates = []
    for number in execution_order:
        if not execution_order_no_duplicates or (execution_order_no_duplicates and execution_order_no_duplicates[-1] != number):
            execution_order_no_duplicates.append(number)

    return execution_order_no_duplicates[1:]

def extract_info_upto_exception(text):
    extracted_data = []
    lines = text.strip().split('\n')
    flag = False
    prev_line = None
    line_number = None
    
    for line in lines:
        if "exception" in line:
            flag = True
            break
        # if "return" in line:
        #     break
        line_number_match = re.search(r':(\d+)', line)
        if line_number_match:
            prev_line = line_number
            line_number = int(line_number_match.group(1)) - 1

        var_value_matches = re.findall(r'\[([^[\]]*(?:\[[^[\]]*])*[^[\]]*)\]', line)

        if not var_value_matches: continue
        var_val = []
        for match in var_value_matches:
            parts = match.split("=>")
            if len(parts) == 2:
                variable = parts[0].strip()
                value = parts[1].strip()
                var_val.append({variable: value})                

        if var_val == []: continue
        extracted_data.append({"line": prev_line , "var_val": var_val})
  
    merged_data = []
    if extracted_data:
        previous_entry = extracted_data[0]
        for current_entry in extracted_data[1:]:
            if previous_entry['line'] == current_entry['line']:
                previous_entry['var_val'].extend(current_entry['var_val'])
            else:
                merged_data.append(previous_entry)
                previous_entry = current_entry
        merged_data.append(previous_entry)

    return merged_data, flag

def get_info_on_exception(text):
    lines = text.strip().split('\n')
    exception_info = None
    variables = []
    
    exception_message_pattern = r"!\s+test_function:\s+\((.*)\)"
    for i, line in enumerate(lines):
        if not "exception" in line: continue
        # Extract line number
        line_number_match = re.search(r':(\d+)', line)
        line_number = line_number_match.group(1) if line_number_match else None

        # Look for variable and value in the same line (if any)
        var_value_matches = re.findall(r'\[([^[\]]*(?:\[[^[\]]*])*[^[\]]*)\]', line)

        for match in var_value_matches:
            parts = match.split("=>")
            if len(parts) == 2:
                variable = parts[0].strip()
                value = parts[1].strip()
                variables.append({variable: value})  

        j = i + 1
        while j < len(lines) and lines[j].strip().startswith("..."):
            var_value_matches = re.findall(r'\[([^[\]]*(?:\[[^[\]]*])*[^[\]]*)\]', lines[j])
            for var_value in var_value_matches:
                parts = var_value.split(" => ")
                if len(parts) == 2:
                    variable, value = parts
                    variables.append({variable: value})
            j += 1
        
        # Extract exception message
        exception_message_match = re.search(exception_message_pattern, lines[j] if j < len(lines) else "")
        if exception_message_match:
            exception_message = exception_message_match.group(1)
            exception_message = exception_message.strip("\"'")
            # pattern = r"(<class '.*?'>), (TypeError\(.*?\))"
            pattern = r"(<class '.*?'>), (TypeError\((?:[^()]|\([^()]*\))*?\))"
            match = re.search(pattern, exception_message)
            if match:
                class_info = match.group(1)  
                type_error_message = match.group(2)
            
            # exception_info = {
            #     "line": int(line_number) - 1,
            #     "var_val": variables,
            #     "exception_class": class_info,
            #     "error_message": type_error_message
            # }
            break

    return [{"line" : int(line_number) - 1, "var_val": variables}], [{"exception_class": class_info, "error_message": type_error_message}]
