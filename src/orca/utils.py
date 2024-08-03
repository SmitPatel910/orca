import re
import json
import ast

# Token Tracker
tokens_path = './tokens.json'
def token_tracker(response):
    with open(tokens_path, 'r') as infile:
        token = json.load(infile)
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = response.usage.total_tokens
    estimate_cost = ((prompt_tokens * 0.0010)/1000) + ((completion_tokens * 0.0020)/1000)
    token['input'] += prompt_tokens
    token['output'] += completion_tokens
    token['total_tokens'] += total_tokens
    token['estimate_cost'] += estimate_cost 
    with open(tokens_path, 'w') as outfile:
        json.dump(token, outfile, indent=4)

# Get the Scope of the Branches From the Code
def extract_scopes_with_line_numbers(code):
    tree = ast.parse(code)
    categorized_scopes = {
        'for': [],
        'while': [],
        'if': [],
        'simple_statement': []
    }

    class ScopeExtractor(ast.NodeVisitor):
        def extract_scope(self, node, scope_type):
            start_line = node.lineno
            end_line = node.end_lineno
            scope_code = ast.get_source_segment(code, node)
            categorized_scopes[scope_type].append((start_line, end_line, scope_code))

        def visit_For(self, node):
            self.extract_scope(node, 'for')

        def visit_While(self, node):
            self.extract_scope(node, 'while')

        def visit_If(self, node):
            self.extract_scope(node, 'if')

        def generic_visit(self, node):
            if isinstance(node, ast.Expr) or isinstance(node, ast.Assign) or isinstance(node, ast.AugAssign):
                start_line = node.lineno
                end_line = node.end_lineno
                stmt_code = ast.get_source_segment(code, node)
                categorized_scopes['simple_statement'].append((start_line, end_line, stmt_code))
            super().generic_visit(node)

    ScopeExtractor().visit(tree)
    return categorized_scopes

def get_scope(code):
    for_loop = []
    while_loop = []
    if_statement = []
    simple_statements = []

    categorized_scopes = extract_scopes_with_line_numbers(code)
    for scope_type, scopes in categorized_scopes.items():
        for start_line, end_line, scope in scopes:
            if scope_type == 'for':
                for_loop.append([start_line, end_line])
            elif scope_type == 'while':
                while_loop.append([start_line, end_line])
            elif scope_type == 'if':
                if_statement.append([start_line, end_line])
            else:
                simple_statements.append([start_line, end_line])
        
    return for_loop, while_loop, if_statement, simple_statements

def get_error_block(lines):
    block_pattern = re.compile(r"Block:\s*(\d+)", re.IGNORECASE)
    for line in lines:
        block_match = block_pattern.search(line)
        if block_match:
            block_number = block_match.group(1)
            return block_number
    return None

def fetch_symbol_table(text_block):
    symbol_table_content = ""
    for text_block_line in text_block.split('\n'):
        # Find the symbol table
        lines_with_symbol_tables = re.findall(r'(?i)symbol table:?.*?{.*}', text_block_line)
        for line in lines_with_symbol_tables:
            start_index = line.find('{')
            end_index = line.rfind('}') + 1
            symbol_table_content = line[start_index:end_index]
    try:
        symbol_table = eval(symbol_table_content)
        return symbol_table
    except:
        return ""

def get_the_symbol_table(blocks_list):
    block_id_symbol_table = []
    for block in blocks_list:
        block_id = block['block_id']
        block_content = block['content']
        symbol_table = fetch_symbol_table(block_content)
        if symbol_table == "":
            block_id_symbol_table.append({"block_id": int(block_id), "symbol_table": {}})
        else:
            block_id_symbol_table.append({"block_id": int(block_id), "symbol_table": symbol_table})
    return block_id_symbol_table

# Output Parser
def output_parser(output, response):
    # Keep Track of Tokens
    token_tracker(response)

    # Define a list of keywords to check in the output
    keywords = ['Observation', 'evaluate', 'Error Type', '<END>']
    if not any(keyword in output for keyword in keywords):
        print("Output does not contain any of the keywords: " + ", ".join(keywords))
        return "", ["", ""]
    
    # Initialize the variables
    blocks_list = []
    block_content = []
    block_execution_order = []

    error_type = None
    is_error = False
    error_block = None
    block_started = False
    block_id = None

    lines = output.split('\n')
    for index, line in enumerate(lines):
        
        # Check if the line contains an error
        if 'Is Error' in line:
            if 'true' in line.lower():  is_error = True
        
        # Check if the line contains an error type
        if "Error Type" in line and is_error:
            
            if "None" in line: 
                is_error = False
                break
            
            if "<class 'TypeError'>" in line:
                is_error = True
                error_type = "TypeError"
                error_block = get_error_block(lines[index:])
                break
            else:
                match = re.search(r"Error Type:\s*(\w+)", line)
                if match:   
                    is_error = True
                    error_type = match.group(1).strip()
                    error_block = get_error_block(lines[index:])
                    break
                break

        # Check if current line is a block start
        pattern = r'^Block\s*:?\s*\d+\s*[:]?[ ]?$'
        matches = re.findall(pattern, line)
        if matches:
            if block_started:
                blocks_list.append({"block_id": int(block_id), "content": '\n'.join(block_content)})
                block_content = [] 
            block_started = True
            block_id = int(line[line.find('Block') + 6:].split(':')[0])

        if block_started:
            block_content.append(line)

    if block_started:
        blocks_list.append({"block_id": int(block_id), "content": '\n'.join(block_content)})

    # If can not Fetch the Block Details and Error Details
    if not blocks_list and not is_error and not error_block:
        return [], []
    
    # If Block Details are fetched
    if blocks_list:
        try:
            # Block Execution Order
            for block in blocks_list:
                block_execution_order.append(int(block['block_id']))
        except:
            return [], [], []
        
        # Block Symbol Table
        try:
            blocks_symbol_table = get_the_symbol_table(blocks_list)
        except:
            blocks_symbol_table = []

    if is_error and error_block:
        return block_execution_order, [error_type, error_block, is_error], blocks_symbol_table
    elif is_error and not error_block:
        return block_execution_order, [error_type, "", is_error], blocks_symbol_table
    else:
        return block_execution_order, ["", "", is_error], blocks_symbol_table

# Blocks to Statements
def get_gt_block_execution(ground_truth_blocks):
    execution_order = []
    for line in ground_truth_blocks:
        block_number = line['block']
        execution_order.append(int(block_number))
    return execution_order

def blocks_to_statements(block_range, block_execution):
    statement_execution = []
    for each_block in block_execution:
        block_range_for_current_block = block_range[str(each_block)]['range']
        start_range = block_range_for_current_block[0]
        end_range = block_range_for_current_block[1]
        for i in range(start_range, end_range+1):
            statement_execution.append(i)
    return statement_execution

def get_statements_from_blocks(block_range, prediction_blocks, ground_truth_blocks):
    
    gt_block_exe = get_gt_block_execution(ground_truth_blocks)
    pd_block_exe = prediction_blocks['block_execution']
    gt_statement_execution = blocks_to_statements(block_range, gt_block_exe)
    pd_statement_execution = blocks_to_statements(block_range, pd_block_exe)

    return pd_statement_execution, gt_statement_execution
