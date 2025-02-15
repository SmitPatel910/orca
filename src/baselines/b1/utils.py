import ast

# Parse the output
def output_parser(output):
    lines = output.split("\n")
    error_type = ""
    is_error = False
    statement_exe = []
    try:
        # Iterate over the lines and extract the required information
        for line in lines:
            # If the line contains the Error information
            if "Error:" in line:
                if line.split(":")[1].strip() == "Yes":
                    is_error = True
            # If the line contains the Error Type information
            if line.startswith("Error Type:"):
                if line.split(":")[1].strip():
                    error_type = line.split(":")[1].strip()
            # If the line contains the Execution information
            if "Execution" in line:
                statement_exe_str = line.split(":")[1].strip()
                # Check if the statement_exe_str is a valid python list
                statement_exe = ast.literal_eval(statement_exe_str)
    except Exception as e:
        return None, [None, None]   
    return statement_exe, [error_type, is_error]
