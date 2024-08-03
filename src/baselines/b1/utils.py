import ast

def output_parser(output):
    lines = output.split("\n")
    error_type = ""
    is_error = False
    statement_exe = []
    try:
        for line in lines:
            if "Error:" in line:
                if line.split(":")[1].strip() == "Yes":
                    is_error = True
            if line.startswith("Error Type:"):
                if line.split(":")[1].strip():
                    error_type = line.split(":")[1].strip()
            if "Execution" in line:
                statement_exe_str = line.split(":")[1].strip()
                statement_exe = ast.literal_eval(statement_exe_str)
    except Exception as e:
        return None, [None, None]   
    return statement_exe, [error_type, is_error]

