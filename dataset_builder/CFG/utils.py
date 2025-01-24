import ast
 
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

"""
The functions `get_block_connections`, `process_branch_scopes`, `build_next_block_result`, `find_block_by_scope`, and `extract_scope` work together to extract the connections between blocks in the CFG for each block.
"""
def get_block_connections(block_ranges, cfg):
    '''
    Extract the connections between blocks in a Control Flow Graph (CFG) for each block.

    This function analyzes each block in the CFG to determine its next block(s) based on control flow and conditions:
    - `extract_scope`: Collects the line ranges (scope) for the block.
    - `process_branch_scopes`: Identifies the true, false, and no-condition scopes for a block.
    - `build_next_block_result`: Constructs the next block connection result for a block.

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
    block_connections = {}  # Maps block indices to their next blocks
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
        
        # Identify the starting line of the block which is the block index
        block_index = min(block_line_numbers)

        # Determine the true, false, and no-condition scopes for the block
        true_branch_scope, false_branch_scope, no_condition_scope = process_branch_scopes(block)

        # Build the next block result for the current block
        next_block_result = build_next_block_result(block_ranges, true_branch_scope, false_branch_scope, no_condition_scope)
        block_connections[block_index] = next_block_result

    return block_connections

# Helper function of `get_block_connections`
def process_branch_scopes(block):
    '''
    Determine the true, false, and no-condition scopes for a given block in a Control Flow Graph (CFG).

    This function uses `extract_scope` to extract the scope.
    if the block has branches, it extracts the line ranges for the true and false branches.
    If the block has no branches, it extracts the line ranges for the next connected blocks.

    Arguments:
        cfg_block (CFGBlock): A block from the Control Flow Graph (CFG) to get the branch scope. 

    Returns:
        tuple: A tuple containing:
            - true_branch_scope (list): Line ranges for the true branch of the block.
            - false_branch_scope (list): Line ranges for the false branch of the block.
            - no_condition_scope (list): Line ranges for blocks without conditional branches.
    '''
    true_branch_scope = []  # Scope for the true branch
    false_branch_scope = []  # Scope for the false branch
    no_condition_scope = []  # Scope for blocks without conditions

    if block.branches:
        # Extract line ranges for true and false branches
        true_branch_scope = extract_scope(block.branches[True])
        false_branch_scope = extract_scope(block.branches[False])
    else:
        for next_block in block.next:
            no_condition_scope.extend(extract_scope(next_block))

    return true_branch_scope, false_branch_scope, no_condition_scope

# Helper function of `get_block_connections`
def build_next_block_result(block_ranges, true_branch_scope, false_branch_scope, no_condition_scope):
    '''
    Prepare the next block connection result for a given block in a Control Flow Graph (CFG).

    This function identifies the next blocks for the true, false, and no-condition branches of a block.
    It uses `find_block_by_scope` to find the block index based on the line ranges.

    Arguments:
        block_ranges (dict): A dictionary mapping block indices to their line ranges.
        true_branch_scope (list): Line ranges for the true branch of the block.
        false_branch_scope (list): Line ranges for the false branch of the block.
        no_condition_scope (list): Line ranges for blocks without conditional branches.

    Returns:
        dict: A dictionary containing the next block connections with the following structure:
              {
                  "with_condition": {
                      "true": <Block index or "<END>">,
                      "false": <Block index or "<END>">
                  },
                  "no_condition": <Block index or None>
              }
    '''
    next_block_connections = {
        "with_condition": {"true": None, "false": None},
        "no_condition": None
    }
    # Map true branch scope
    if true_branch_scope:
        next_block_connections["with_condition"]["true"] = find_block_by_scope(block_ranges, true_branch_scope)
    else:
        next_block_connections["with_condition"]["true"] = "<END>"

    # Map false branch scope
    if false_branch_scope:
        next_block_connections["with_condition"]["false"] = find_block_by_scope(block_ranges, false_branch_scope)
    else:
        next_block_connections["with_condition"]["false"] = "<END>"

    # Map no condition scope
    if no_condition_scope:
        next_block_connections["no_condition"] = find_block_by_scope(block_ranges, no_condition_scope)
    
    return next_block_connections

# Helper function of `build_next_block_result`
def find_block_by_scope(block_ranges, scope_line_numbers):
    '''
    Find the block index corresponding to a given scope of line numbers.

    This function searches the `block_ranges` dictionary to find the block whose range
    matches the minimum and maximum line numbers in the provided scope.

    Arguments:
        block_ranges (dict): A dictionary mapping block indices to their line ranges.
        scope_line_numbers (list): A list of line numbers defining the scope to search for.

    Returns:
        int or None: The block index if a matching block is found; otherwise, `None`.
    '''
    # Determine the minimum and maximum line numbers from the scope
    min_line_number = min(scope_line_numbers)
    max_line_number = max(scope_line_numbers)
    for block_index, block_data in block_ranges.items():
        if block_data['range'] == [min_line_number, max_line_number]:
            return block_index
    # Return None if no matching block is found
    return None

# Helper function of `get_block_ranges_and_statements` and `get_block_connections`
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

def map_execution_order_to_blockwise(cfg_block_range, execution_order, execution_trace):
    '''
    Convert line wise execution trace to block wise execution trace.

    Arguments:
        cfg_block_range (dict): A dictionary mapping block IDs to their line ranges.
        execution_order (list): A list of line numbers representing the order of execution.
            Example: [1, 2, 3, 5, ...]
        execution_trace (list): A list of dictionaries containing trace information for each line.
            Example: [{'line': 1, 'var_val': {'x': 1, 'y': 'res'}}, {'line': 2, 'var_val': {'x': 3, 'y': 'res'}}, ...]
    
    Returns:
        list: A list of dictionaries representing blocks wise execution trace.
            Example: [{'block': 'Block 1', 'state':{'x': 1, 'y': 'res'}}, {'block': 'Block 2', 'state': {'x': 3, 'y': 'res'}}, ...]
    '''
    execution_blocks = []

    # Step 1: Combine execution order and trace information
    combined_execution_trace = []
    for index, line_number in enumerate(execution_order):
        try:
            trace_line_number = int(execution_trace[index]['line'])
            if trace_line_number == int(line_number):
                variable_state = execution_trace[index]['var_val']
                combined_execution_trace.append({"line_number": trace_line_number, "state": variable_state})
            else:
                combined_execution_trace.append({"line_number": int(line_number), "state": []})
        except Exception as e:
            combined_execution_trace.append({"line_number": int(line_number), "state": []})

    # Step 2: Map block ranges for easier lookup
    blocks_ranges = {}
    for each_block in cfg_block_range:
        range = cfg_block_range[each_block]['range']
        min_line = range[0]; max_line = range[1]
        blocks_ranges[each_block] = [min_line, max_line]
    
    # Step 3: Generate block wise execution trace
    last_block = None
    for entry in combined_execution_trace:
        line_number = entry['line_number']
        state = entry['state']
        for block_name, range_ in blocks_ranges.items():
            if range_[0] <= line_number <= range_[1]:
                if last_block == block_name: 
                    execution_blocks[-1] = {"block" : block_name, "state" : state}
                else:
                    execution_blocks.append({"block" : block_name, "state" : state})
                    last_block = block_name
                break

    return execution_blocks

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
