import ast
import re

# Get the symbol table from the output
def get_symbol_table(lines):
    # Iterate over the lines and extract the symbol table
    for line in lines:
        lines_with_symbol_tables = re.findall(r'(?i)symbol table:?.*?{.*}', line)
        # If the line contains the symbol table
        for line in lines_with_symbol_tables:
            start_index = line.find('{')
            end_index = line.rfind('}') + 1
            symbol_table_content = line[start_index:end_index]
        try:
            # Check if the symbol table is a valid python dictionary
            symbol_table = eval(symbol_table_content)
            return symbol_table
        except:
            return ""

# Parse the output   
def output_parser(output):
    lines = output.split("\n")
    error_type = ""
    symbol_table = ""
    is_error = False
    statement_exe = []

    try:
        # Iterate over the lines and extract the required information
        for index, line in enumerate(lines):
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
                statement_exe = ast.literal_eval(statement_exe_str)
            # If the line contains the Symbol Table information
            if "Symbol Table:" in line:
                fetched_lines = lines[index:]
                symbol_table = get_symbol_table(fetched_lines)
                
    except Exception as e:
        return None, [None, None], None
    
    return statement_exe, [error_type, is_error], symbol_table
