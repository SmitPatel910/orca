import re
import ast

# CFG Generation
def replace_code_in_file(filePath, code):
    '''Replace occurrences of "TestString" with the given indented code.

    Arguments:
        filePath (str): The path to the file where the replacement will be performed.
        code (str): The code to replace "TestString".

    Returns:
        None: The function modifies the file in place and does not return any value.
    '''
    with open(filePath, 'r') as file:
        content = file.read()
    
    # Intend the code
    indented_code = '\n'.join(['    ' + line for line in code.splitlines()])
    # Replace the TestString with the indented code
    content = content.replace('TestString', indented_code)
    
    # Write the content back to the file
    with open(filePath, 'w') as file:
        file.write(content)
        
def reset_file_content(filePath):
    '''Reset the content of the file to a predefined content.

    Arguments:
        filePath (str): The path to the file to be reset.

    Returns:
        None: The function modifies the file in place and does not return any value.
    '''

    # Predefined content
    content = """def testFun():
TestString"""

    # Write the content back to the file
    with open(filePath, 'w') as file:
        file.write(content)

"""
The functions 'get_block_ranges_and_statements', 'extract_scope', and 'transform_statement_with_ast' work together to extract line ranges (scope) and transformed statements for each block in the CFG.
"""
def get_block_ranges_and_statements(cfg, code):
    '''
    Extract block ranges and transformed statements from a Control Flow Graph (CFG).

    This function iterates through each block in the CFG:
    - `extract_scope`: Collects the line ranges (scope) for the block.
    = `transform_statement_with_ast`: Transforms the statement using the AST module.

    Arguments:
        cfg (object): The Control Flow Graph containing blocks to analyze.
        code (str): The source code corresponding to the CFG.

    Returns:
        tuple: A tuple containing:
            - block_ranges (dict): A dictionary mapping block indices to their line ranges.
            - block_statements (dict): A dictionary mapping block indices to lists of
              transformed statements.
        None: If an error occurs during processing, returns `None, None`.
    '''
    block_ranges = {}  # Maps block indices to line ranges
    block_statements = {}  # Maps block indices to transformed statements
    is_processing_started = False  # Tracks whether processing should start

    for block in cfg.blocks:
        # Start processing blocks after the 'testFun' definition
        if block.label == "<entry:testFun>": 
            is_processing_started = True
        if not is_processing_started: 
            continue
        
        # Skip blocks without control flow nodes
        if len(block.control_flow_nodes) == 0: 
            continue
        
        # Skip blocks leading to error-raising blocks
        for next_block in block.next:
            if next_block.label == "<raise>": 
                continue
        
        # Extract the line numbers associated with the current block
        block_line_numbers = extract_scope(block)

        # Map block index to its range of lines
        block_start_line = min(block_line_numbers)
        block_ranges[block_start_line] = {"range": [min(block_line_numbers), max(block_line_numbers)]}
        
        # Collect transformed statements for the current block
        transformed_statements = []
        for line_number in block_line_numbers:
            transformed_statement = transform_statement_with_ast(code, line_number)
            if transformed_statement is None: 
                return None, None
            transformed_statements.append(transformed_statement)
        block_statements[block_start_line] = transformed_statements
    
    return block_ranges, block_statements

# Helper function of `get_block_ranges_and_statements`
def transform_statement_with_ast(source_code, target_line_number):
    '''
    Transform a statement in the source code using the AST module.

    Arguments:
        source_code (str): The source code corresponding to the CFG.
        target_line_number (int): The line number of the statement to transform.
    
    Returns:
        str: The transformed statement.
        None: If an error occurs during transformation, returns `None`.
    '''
    try:
        class ASTStatementVisitor(ast.NodeVisitor):
            def __init__(self, target_line_number):
                self.target_line_number = target_line_number
                self.transformed_result = None
 
            def visit_For(self, node):
                if node.lineno == self.target_line_number:
                    if isinstance(node.target, ast.Tuple):
                        variable_names = [elt.id for elt in node.target.elts]
                        index_variable = variable_names[0]
                        iterator_variable = variable_names[1]
                        self.transformed_result = f"{index_variable} <- index\n    {iterator_variable} <- iterator"
                    else:
                        iterator_variable = node.target.id
                        iterable_expression = ast.unparse(node.iter)
                        self.transformed_result = f"iterator -> {iterator_variable}, Iterate Over -> {iterable_expression}"
                self.generic_visit(node)
 
            def visit_If(self, node):
                if node.lineno == self.target_line_number:
                    condition_expression = ast.unparse(node.test)
                    self.transformed_result = f"({condition_expression})"
                self.generic_visit(node)

        # Parse the source code into an AST and visit the nodes
        syntax_tree = ast.parse(source_code)
        statement_visitor = ASTStatementVisitor(target_line_number)
        statement_visitor.visit(syntax_tree)

        # Return the transformed result or the original line if no transformation occurred
        if statement_visitor.transformed_result is None:
            return source_code.split('\n')[target_line_number - 1].strip()
        else:
            return statement_visitor.transformed_result
        
    except Exception as e:
        return None

# Helper function of `get_block_ranges_and_statements`
def extract_scope(block):
    '''
    Extract the line numbers (scope) of the block from the Control Flow Graph (CFG).

    Arguments:
        block (CFGBlock): A block from the Control Flow Graph (CFG) containing control flow nodes.
    
    Returns:
        list: A list of line numbers corresponding to the control flow nodes in the block.
    '''
    scope_line_numbers = []
    for node in block.control_flow_nodes:
        instruction = node.instruction
        ast_node = instruction.node
        line_number = ast_node.lineno
        scope_line_numbers.append(line_number - 1) # Adjust to zero-based indexing
    
    return scope_line_numbers

def get_block_connections(block_ranges, cfg):
    '''
    Extract the connections between blocks in a Control Flow Graph (CFG) for each block.

    Arguments:
        block_ranges (dict): A dictionary mapping block indices to their line ranges (scope).
        cfg (object): The Control Flow Graph containing the blocks to analyze.

    Returns:
        dict: A dictionary where the keys are block indices, and the values are dictionaries specifying the connections.
        Example:
            {
                block_index: {
                    "with_condition": {
                        "true": next_block_index,
                        "false": next_block_index
                    },
                    "no_condition": next_block_index
                }
            }
    '''
    block_connections = {}
    is_processing_started = False

    for block in cfg.blocks:
        # Initialize variables
        true_scope_block = []; false_scope_block = []; no_condition_block_lines = []; true_next = None; false_next = None; no_condition_next = None

        # Start processing blocks after the 'testFun' definition
        if block.label == "<entry:testFun>": 
            is_processing_started = True
        if not is_processing_started: 
            continue

        # Skip blocks without control flow nodes
        if len(block.control_flow_nodes) == 0: 
            continue
        
        # Skip blocks leading to error-raising blocks
        for next_block in block.next:
            if next_block.label == "<raise>": 
                continue

        # Filtered Block
        line_number_list = []
        for node in block.control_flow_nodes:
            instruction = node.instruction
            ast_node = instruction.node
            line_number = ast_node.lineno
            line_number_list.append(line_number-1)
        
        # Get the block index
        block_index = min(line_number_list)

        if block.branches: # Block with branches
            true_block = block.branches[True]
            false_block = block.branches[False]
            for node in true_block.control_flow_nodes:
                instruction = node.instruction
                ast_node = instruction.node
                line_number = ast_node.lineno
                true_scope_block.append(line_number-1)

            for node in false_block.control_flow_nodes:
                instruction = node.instruction
                ast_node = instruction.node
                line_number = ast_node.lineno
                false_scope_block.append(line_number-1)
        else: # Block with no branches
            for next_block in block.next:
                for node in next_block.control_flow_nodes:
                    instruction = node.instruction
                    ast_node = instruction.node
                    line_number = ast_node.lineno
                    no_condition_block_lines.append(line_number-1)
        
        if true_scope_block and false_scope_block:
            # True Scope
            min_line_number = min(true_scope_block)
            max_line_number = max(true_scope_block)
            for key, value in block_ranges.items():
                if value['range'] == [min_line_number, max_line_number]:
                    true_next = key
                    break
            # False Scope
            min_line_number = min(false_scope_block)
            max_line_number = max(false_scope_block)
            for key, value in block_ranges.items():
                if value['range'] == [min_line_number, max_line_number]:
                    false_next = key
                    break
        elif true_scope_block: # Block with True Scope
            min_line_number = min(true_scope_block)
            max_line_number = max(true_scope_block)
            for key, value in block_ranges.items():
                if value['range'] == [min_line_number, max_line_number]:
                    true_next = key
                    false_next = "<END>"
                    break
        elif false_scope_block: # Block with False Scope
            min_line_number = min(false_scope_block)
            max_line_number = max(false_scope_block)
            for key, value in block_ranges.items():
                if value['range'] == [min_line_number, max_line_number]:
                    true_next = "<END>"
                    false_next = key
                    break
        else:  # Block with No Condition
            if not no_condition_block_lines: continue
            min_line_number = min(no_condition_block_lines)
            max_line_number = max(no_condition_block_lines)
            for key, value in block_ranges.items():
                if value['range'] == [min_line_number, max_line_number]:
                    no_condition_next = key
                    break
        
        # Store the block connections
        block_connections[block_index] = {
            "with_condition": {"true": true_next, "false": false_next} ,  
            "no_condition": no_condition_next
        }
 
    return block_connections

def renumber_cfg_blocks(cfg_block_statements, cfg_block_range, cfg_block_connection):
    '''Renumber blocks in a control flow graph (CFG) and handle special cases for loop blocks.

    Arguments:
        cfg_block_statements (dict): A dictionary mapping block IDs to their statements.
        cfg_block_range (dict): A dictionary mapping block IDs to their range information.
        cfg_block_connection (dict): A dictionary mapping block IDs to their connections.

    Returns:
        tuple: Updated dictionaries for block statements, block ranges, and next block connections.
    '''
    # Step 1: Renumber block statements
    sorted_block_statements = {k: cfg_block_statements[k] for k in sorted(cfg_block_statements)}
    renumbering_dict = {old: new for new, old in enumerate(sorted_block_statements, start=1)}
    new_cfg_block_statements = {
        renumbering_dict[block_id]: statements for block_id, statements in sorted_block_statements.items()
    }

    # Step 2: Renumber block ranges
    sorted_block_ranges = {k: cfg_block_range[k] for k in sorted(cfg_block_range)}
    new_cfg_block_ranges = {
        renumbering_dict[block_id]: block_range for block_id, block_range in sorted_block_ranges.items()
    }

    # Step 3: Renumber next block connections
    new_cfg_block_connection = {}
    for old_block, connections in cfg_block_connection.items():
        new_block = renumbering_dict[old_block]
        new_cfg_block_connection[new_block] = {}
        for condition, target in connections.items():
            if condition == "no_condition":
                if target == "<END>":
                    new_cfg_block_connection[new_block][condition] = "<END>"
                elif target is not None:
                    new_cfg_block_connection[new_block][condition] = renumbering_dict.get(target, None)
                else:
                    new_cfg_block_connection[new_block][condition] = None
            else:
                # with_condition case
                new_cfg_block_connection[new_block][condition] = {}
                for branch, target_block in target.items():
                    if target_block == "<END>":
                        new_cfg_block_connection[new_block][condition][branch] = "<END>"
                    elif target_block is not None:
                        new_cfg_block_connection[new_block][condition][branch] = renumbering_dict.get(target_block, None)
                    else:
                        new_cfg_block_connection[new_block][condition][branch] = None

    # Special Case to Handle the For Loop (keep iterator and iterate over in only one block)
    keys = list(new_cfg_block_statements.keys())[:-1]
    for key in keys:
        # Check if the next block has only one statement by checking the statement length
        block_length = len(new_cfg_block_statements[key + 1])
        # Check if the next block has only one statement by checking block range
        block_start, block_end = new_cfg_block_ranges[key + 1]['range']
        
        # Check if the current block's last statement is the same as the next block's first statement
        curr_block_last_statement = new_cfg_block_statements[key][-1]
        next_block_first_statement = new_cfg_block_statements[key + 1][0]
        # Check if the current block's last line number and the next block's first line number are same
        curr_block_last_line_number = new_cfg_block_ranges[key]['range'][1]
        next_block_first_line_number = new_cfg_block_ranges[key + 1]['range'][0]

        if block_length == 1 and block_start == block_end:
            if curr_block_last_statement == next_block_first_statement and curr_block_last_line_number == next_block_first_line_number:
                if 'iterator' in new_cfg_block_statements[key][-1] and 'iterator' in new_cfg_block_statements[key + 1][0]:
                    new_cfg_block_statements[key] = new_cfg_block_statements[key][:-1]
                    start_range, end_range = new_cfg_block_ranges[key]['range']
                    new_cfg_block_ranges[key]['range'] = [start_range, end_range - 1]

    return new_cfg_block_statements, new_cfg_block_ranges, new_cfg_block_connection

def generate_cfg_text(block_statements, next_block_connections, block_ranges):
    '''Generate a textual representation of a control flow graph (CFG) from its block data.
    
    Arguments:
        block_statements (dict): A dictionary mapping block indices to their statements.
            Example: {1: ["x = 1", "y = 2", "(x < y)"], 2: ["z = x + y"], ...}
        next_block_connections (dict): A dictionary mapping block indices to their next block connections.
            Example: {1: {"with_condition": {"true": 2, "false": 3}, "no_condition": None}, ...}
        block_ranges (dict): A dictionary mapping block indices to their line ranges.
            Example: {1: {"range": [1, 3]}, 2: {"range": [4, 5]}}
    
    Returns:
        str: A textual representation of the CFG. If the block data is inconsistent, returns an empty string.
    '''
    cfg_text = ""
    for block_index in block_ranges:
        # Add block header
        cfg_text += f"\nBlock {block_index}:\n"

        # Extract and validate range and statements
        block_range = block_ranges[block_index]["range"]
        start_line, end_line = block_range[0], block_range[1]
        total_lines = end_line - start_line + 1
        statements = block_statements[block_index]

        if len(statements) != total_lines:
            # Inconsistent block data, return empty string
            return ""
        
        # Add block statements
        cfg_text += "Statements:"
        for statement in statements:
            cfg_text += f"\n    {statement}"

        # Add next block connections
        cfg_text += "\nNext:\n"
        try:
            next_blocks = next_block_connections[block_index]
            true_next = next_blocks["with_condition"]["true"]
            false_next = next_blocks["with_condition"]["false"]
            no_condition_next = next_blocks["no_condition"]

            # True condition
            if true_next is not None:
                if true_next == "<END>":
                    cfg_text += "    <END>\n"
                else:   
                    cfg_text += f"    If True: Go to Block {true_next}\n"

            # False condition
            if false_next is not None:
                if false_next == "<END>":
                    cfg_text += "    <END>\n"
                else:   
                    cfg_text += f"    If False: Go to Block {false_next}\n"

            # If Both (True and False) are exits then no scope for no_condition
            if true_next and false_next: continue

            # No condition
            if not true_next and not false_next:
                if no_condition_next == "<END>":
                    cfg_text += "    <END>\n"
                else:   
                    cfg_text += f"    Go to Block {no_condition_next}\n"
        except:
            # If next block connections are missing, It means the block is the last block
            cfg_text += "    <END>\n"
    
    return cfg_text

# ORCA Pipeline
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
def output_parser(output):
    '''Parse the output from the GPT model to extract block execution order, error details, and symbol table.

    Args:
        output (str): The raw output from the GPT model.

    Returns:
        tuple: Contains:
            - block_execution_order (list): List of executed block IDs in order.
            - error_details (list): Error type, error block, and error flag (e.g., ["TypeError", 3, True]).
            - blocks_symbol_table (list): Symbol table for each block.
    '''

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

def clean_response(obj):
    """Recursively clean the response object to make it JSON-serializable."""
    if isinstance(obj, dict):
        return {k: clean_response(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_response(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(clean_response(item) for item in obj)
    elif isinstance(obj, type):
        return str(obj.__name__)  # Convert <class 'int'> to 'int'
    else:
        return obj