import ast
import re

def get_symbol_table(lines):
    for line in lines:
        lines_with_symbol_tables = re.findall(r'(?i)symbol table:?.*?{.*}', line)
        for line in lines_with_symbol_tables:
            start_index = line.find('{')
            end_index = line.rfind('}') + 1
            symbol_table_content = line[start_index:end_index]
        try:
            symbol_table = eval(symbol_table_content)
            return symbol_table
        except:
            return ""
    
def output_parser(output):
    lines = output.split("\n")
    error_type = ""
    symbol_table = ""
    is_error = False
    statement_exe = []
    try:
        for index, line in enumerate(lines):
            if "Error:" in line:
                if line.split(":")[1].strip() == "Yes":
                    is_error = True
            if line.startswith("Error Type:"):
                if line.split(":")[1].strip():
                    error_type = line.split(":")[1].strip()
            if "Execution" in line:
                statement_exe_str = line.split(":")[1].strip()
                statement_exe = ast.literal_eval(statement_exe_str)
            if "Symbol Table:" in line:
                fetched_lines = lines[index:]
                symbol_table = get_symbol_table(fetched_lines)
                
    except Exception as e:
        return None, [None, None], None
    
    return statement_exe, [error_type, is_error], symbol_table
            