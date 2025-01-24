import re
import json
import ast

# Token Tracker
tokens_path = './tokens.json'
def token_tracker(response):
    '''Track the tokens used in the response and update the tokens.json file.
       It caches tokens used in 'input' and 'output' and updates the total tokens used.
       Also, it estimates the cost of the API call based on the tokens used.
    '''
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
    '''Extract code scopes with their line numbers from Python source code.

    This function parses the given Python source code to identify and extract 
    various types of scopes (e.g., loops, conditional blocks, and simple statements). 
    It returns the start line, end line, and source code for each identified scope.

    Args:
        code (str): The Python source code as a string.

    Returns:
        dict: A dictionary categorizing scopes with the following structure:
            {
                'for': [(start_line, end_line, scope_code), ...],
                'while': [(start_line, end_line, scope_code), ...],
                'if': [(start_line, end_line, scope_code), ...],
                'simple_statement': [(start_line, end_line, statement_code), ...]
            }
    '''
    # Parse the code to an Abstract Syntax Tree (AST)
    tree = ast.parse(code)

    # Initialize a dictionary to store categorized scopes
    categorized_scopes = {
        'for': [], # Store all 'for' loop scopes
        'while': [], # Store all 'while' loop scopes
        'if': [], # Store all 'if' conditional scopes
        'simple_statement': [] # Store all simple statement scopes
    }
    # Custom AST NodeVisitor to extract scopes
    class ScopeExtractor(ast.NodeVisitor):
        def extract_scope(self, node, scope_type):
            # Get the start and end line numbers of the scope
            start_line = node.lineno
            end_line = node.end_lineno
            # Get the source code of the scope
            scope_code = ast.get_source_segment(code, node)
            # Append the scope details to the corresponding category
            categorized_scopes[scope_type].append((start_line, end_line, scope_code))

        # Visit 'for' loops and extract their scopes
        def visit_For(self, node):
            self.extract_scope(node, 'for')

        # Visit 'while' loops and extract their scopes
        def visit_While(self, node):
            self.extract_scope(node, 'while')

        # Visit 'if' conditional blocks and extract their scopes
        def visit_If(self, node):
            self.extract_scope(node, 'if')

        # Handle simple statements (e.g., expressions, assignments)
        def generic_visit(self, node):
            if isinstance(node, ast.Expr) or isinstance(node, ast.Assign) or isinstance(node, ast.AugAssign):
                # Get the start and end line numbers of the statement
                start_line = node.lineno
                end_line = node.end_lineno
                # Get the source code of the statement
                stmt_code = ast.get_source_segment(code, node)
                # Append the statement details to the 'simple_statement' category
                categorized_scopes['simple_statement'].append((start_line, end_line, stmt_code))
            # Continue traversing the AST
            super().generic_visit(node)
    
    # Traverse the AST using the custom visitor
    ScopeExtractor().visit(tree)
    return categorized_scopes

def get_scope(code):
    '''Extract and categorize code scopes into loops, conditionals, and simple statements.

    This function uses the `extract_scopes_with_line_numbers` function to parse Python source code 
    and categorize scopes into `for` loops, `while` loops, `if` statements, and simple statements.
    Each scope is returned as a list of its start and end line numbers.

    Args:
        code (str): The Python source code as a string.

    Returns:
        tuple: Four lists containing:
            - for_loop (list): Start and end line numbers of `for` loops.
            - while_loop (list): Start and end line numbers of `while` loops.
            - if_statement (list): Start and end line numbers of `if` statements.
            - simple_statements (list): Start and end line numbers of simple statements.
    '''
    # Initialize lists for storing different scope types
    for_loop = []
    while_loop = [] 
    if_statement = []
    simple_statements = []

    # Use helper function to extract scopes with line numbers
    categorized_scopes = extract_scopes_with_line_numbers(code)

    # Iterate over each scope type and its corresponding scopes
    for scope_type, scopes in categorized_scopes.items():
        for start_line, end_line, scope in scopes:
            if scope_type == 'for':
                for_loop.append([start_line, end_line]) # Add 'for' loop lines
            elif scope_type == 'while':
                while_loop.append([start_line, end_line]) # Add 'while' loop lines
            elif scope_type == 'if':
                if_statement.append([start_line, end_line]) # Add 'if' statement lines
            else:
                simple_statements.append([start_line, end_line]) # Add simple statement lines
    
    # Return all categorized scopes
    return for_loop, while_loop, if_statement, simple_statements

def get_error_block(lines):
    '''Extract the block number associated with an error from a list of lines.

    This function scans a list of lines to find the first occurrence of a block 
    number following the pattern "Block: <number>". If a match is found, it 
    returns the block number. If no match is found, it returns `None`.

    Args:
        lines (list): A list of strings, each representing a line of text.

    Returns:
        str or None: 
            - The block number as a string if a match is found.
            - `None` if no block number is found.
    '''
    # Compile a regex pattern to match "Block: <number>" (case-insensitive)
    block_pattern = re.compile(r"Block:\s*(\d+)", re.IGNORECASE)
    # Loop through each line in the input list
    for line in lines:
        # Search for the block pattern in the current line
        block_match = block_pattern.search(line)
        if block_match:
            # If a match is found, extract and return the block number
            block_number = block_match.group(1)
            return block_number
    # Return None if no block number is found
    return None

def fetch_symbol_table(text_block):
    '''Extract the symbol table from a given block of text.

    This function scans a text block for lines containing a symbol table in the format:
    "Symbol Table: {...}" or similar. It extracts the symbol table content, evaluates it,
    and returns it as a dictionary. If no symbol table is found or an error occurs, it
    returns an empty string.

    Args:
        text_block (str): A block of text containing potential symbol table information.

    Returns:
        dict or str: 
            - A dictionary representing the symbol table if successfully extracted and evaluated.
            - An empty string if no valid symbol table is found or if an error occurs.
    '''
    
    # Initialize variable to store symbol table content
    symbol_table_content = ""
    
    # Process each line in the text block
    for text_block_line in text_block.split('\n'):
        # Look for lines containing "Symbol Table: {...}"
        lines_with_symbol_tables = re.findall(r'(?i)symbol table:?.*?{.*}', text_block_line)
        
        # Extract content inside the curly braces
        for line in lines_with_symbol_tables:
            start_index = line.find('{') # Find the starting index of '{'
            end_index = line.rfind('}') + 1 # Find the ending index of '}'
            symbol_table_content = line[start_index:end_index]
    
    try:
        # Make sure the symbol table is python dictionary
        symbol_table = eval(symbol_table_content)
        return symbol_table
    except:
        # Return an empty string if evaluation fails
        return ""

def get_the_symbol_table(blocks_list):
    '''Extract symbol tables from each block in the list.

    This function processes a list of blocks and extracts the symbol table 
    for each block using the `fetch_symbol_table` function. If a block does 
    not have a symbol table, it assigns an empty dictionary.

    Args:
        blocks_list (list): A list of dictionaries where each dictionary contains:
            - "block_id" (int): The ID of the block.
            - "content" (str): The content of the block.

    Returns:
        list: A list of dictionaries where each dictionary contains:
            - "block_id" (int): The ID of the block.
            - "symbol_table" (dict): The symbol table for the block (empty if none found).
    '''
    # Initialize a list to store symbol tables for each block
    block_id_symbol_table = []
    # Loop through each block in the list
    for block in blocks_list:
        block_id = block['block_id'] # Get the block ID
        block_content = block['content'] # Get the content of the block

        # Fetch the symbol table for the block content
        symbol_table = fetch_symbol_table(block_content)

        # If no symbol table is found, add an empty dictionary
        if symbol_table == "":
            block_id_symbol_table.append({"block_id": int(block_id), "symbol_table": {}})
        else:
            block_id_symbol_table.append({"block_id": int(block_id), "symbol_table": symbol_table})
    
    return block_id_symbol_table

# Output Parser
def output_parser(output, response):
    '''Parse the output from the GPT model to extract block execution order, error details, and symbol table.

    Args:
        output (str): The raw output from the GPT model.
        response (object): The response object to track tokens.

    Returns:
        tuple: Contains:
            - block_execution_order (list): List of executed block IDs in order.
            - error_details (list): Error type, error block, and error flag (e.g., ["TypeError", 3, True]).
            - blocks_symbol_table (list): Symbol table for each block.
    '''

    # Track tokens used in the response
    token_tracker(response)

    # Check if output contains any required keywords
    keywords = ['Observation', 'evaluate', 'Error Type', '<END>']
    if not any(keyword in output for keyword in keywords):
        print("Output missing keywords: " + ", ".join(keywords))
        return "", ["", ""]
    
    # Initialize the variables
    blocks_list = []  # Stores block details
    block_content = []  # Stores content of each block
    block_execution_order = []  # Stores order of block execution
    error_type = None  # Type of error (if any)
    is_error = False  # Flag indicating if an error occurred
    error_block = None  # Block where the error occurred
    block_started = False  # Indicates if we are inside a block
    block_id = None  # ID of the current block

    # Split output into lines and process each line
    lines = output.split('\n')
    for index, line in enumerate(lines):
        # Check if the output indicates an error
        if 'Is Error' in line and 'true' in line.lower():
            is_error = True
        
        # Extract error type and block if an error occurred
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

        # Detect the start of a block
        pattern = r'^Block\s*:?\s*\d+\s*[:]?[ ]?$'
        matches = re.findall(pattern, line)
        if matches:
            # Save previous block if a new block starts
            if block_started:
                blocks_list.append({"block_id": int(block_id), "content": '\n'.join(block_content)})
                block_content = []  # Reset block content for the new block
            block_started = True
            block_id = int(line[line.find('Block') + 6:].split(':')[0])
        
        # Add lines to the current block content
        if block_started:
            block_content.append(line)
    
    # Add the last block to the list
    if block_started:
        blocks_list.append({"block_id": int(block_id), "content": '\n'.join(block_content)})

    # If no blocks or errors were found
    if not blocks_list and not is_error and not error_block:
        return [], []
    
    # Process block execution details
    if blocks_list:
        try:
            for block in blocks_list:
                block_execution_order.append(int(block['block_id']))
        except:
            return [], [], []
        
        # Block Symbol Table
        try:
            blocks_symbol_table = get_the_symbol_table(blocks_list)
        except:
            blocks_symbol_table = []

    # Return based on whether errors were found
    if is_error and error_block:
        return block_execution_order, [error_type, error_block, is_error], blocks_symbol_table
    elif is_error and not error_block:
        return block_execution_order, [error_type, "", is_error], blocks_symbol_table
    else:
        return block_execution_order, ["", "", is_error], blocks_symbol_table

# Extract the Block Execution Order from the Trace
def get_gt_block_execution(ground_truth_blocks):
    execution_order = []
    for line in ground_truth_blocks:
        block_number = line['block']
        execution_order.append(int(block_number))
    return execution_order

# Convert Block Execution Order to Statement Execution Order
def blocks_to_statements(block_range, block_execution):
    '''Convert block execution order to statement execution order.
       
    Args:
        block_range (dict): The range of statements in each block.
        block_execution (list): The block execution order.
    
    Returns:
        statement_execution (list): The statement execution order.
    '''
    statement_execution = []
    for each_block in block_execution:
        block_range_for_current_block = block_range[str(each_block)]['range']
        start_range = block_range_for_current_block[0]
        end_range = block_range_for_current_block[1]
        for i in range(start_range, end_range+1):
            statement_execution.append(i)
    return statement_execution

# Get the Statement Execution Order from the Block Execution Order
def get_statements_from_blocks(block_range, prediction_blocks, ground_truth_execution_trace):
    '''Get the statement execution order from the block execution order.

    Args:
        block_range (dict): The range of statements in each block.
        prediction_blocks (dict): The prediction blocks.
        ground_truth_execution_trace (list): The ground truth execution trace.

    Returns:
        tuple: A tuple containing:
            - pd_statement_execution (list): The statement execution order from the block level prediction.
            - gt_statement_execution (list): The statement execution order from the block level ground truth.
    '''    
    # Get the block execution order
    gt_block_exe = get_gt_block_execution(ground_truth_execution_trace)
    pd_block_exe = prediction_blocks['block_execution']
    # From the block execution order, get the statement execution order
    gt_statement_execution = blocks_to_statements(block_range, gt_block_exe)
    pd_statement_execution = blocks_to_statements(block_range, pd_block_exe)

    return pd_statement_execution, gt_statement_execution
