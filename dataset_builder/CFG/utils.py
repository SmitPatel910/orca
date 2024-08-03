import ast
 
def replace_code_in_file(filename, code):
    with open(filename, 'r') as file:
        content = file.read()
        
    indented_code = '\n'.join(['    ' + line for line in code.splitlines()])
    content = content.replace('TestString', indented_code)
 
    with open(filename, 'w') as file:
        file.write(content)
        
def reset_file_content(filename):
    content = """def testFun():
TestString"""
    with open(filename, 'w') as file:
        file.write(content)

# Function 1
def extract_statements_range_from_block(cfg, code):
    block_range = {}; block_statement = {}; flag = False
 
    for block in cfg.blocks:
        # Ignore the block having testFun defination
        if block.label == "<entry:testFun>": flag = True
        if not flag: continue
        
        # Ignore the Block with No Control Flow
        if len(block.control_flow_nodes) == 0 : continue
        
        # Ignore the Error Raise Block
        for next_block in block.next:
            if next_block.label == "<raise>": continue
        
        # Get the Line Number of the Block
        block_lines = extract_scope(block)

        # Block-Range
        block_index = min(block_lines)
        block_range[block_index] = {"range": [min(block_lines), max(block_lines)]}
        
        # Block-Statement
        statements = []
        for line_no in block_lines:
            # Transform the Statement
            transformed_statement = statement_transformation(code, line_no)
            if transformed_statement == None: return None, None
            statements.append(transformed_statement)
        block_statement[block_index] = statements
    
    return block_range, block_statement

# Function 1 (Helper)
def statement_transformation(source_code, line_number):
    try:
        class CustomNodeVisitor(ast.NodeVisitor):
            def __init__(self, line_number):
                self.line_number = line_number
                self.result = None
 
            def visit_For(self, node):
                if node.lineno == self.line_number:
                    if isinstance(node.target, ast.Tuple):
                        elements = [elt.id for elt in node.target.elts]
                        index = elements[0]
                        iterator = elements[1]
                        self.result = f"{index} <- index\n    {iterator} <- iterator"
                    else:
                        iterator = node.target.id
                        target = ast.unparse(node.iter)
                        self.result = f"iterator -> {iterator}, Iterate Over -> {target}"
                    
                    # target = ast.unparse(node.iter)
                    # self.result += f"\n    {target} <- iterable"
                self.generic_visit(node)
 
            def visit_If(self, node):
                if node.lineno == self.line_number:
                    condition = ast.unparse(node.test)
                    self.result = f"({condition})"
                self.generic_visit(node)
 
        tree = ast.parse(source_code)
        visitor = CustomNodeVisitor(line_number)
        visitor.visit(tree)
        if visitor.result == None : return source_code.split('\n')[line_number-1].strip()
        else: return visitor.result

    except:
        return None

# =======================================================

# Function 2
def get_the_next_block(block_range, cfg):
    next_block_dict = {}
    is_test_function = False

    for block in cfg.blocks:
        # Ignore the block having testFun defination
        if block.label == "<entry:testFun>":
            is_test_function = True
        
        # Ignore the Block with No Control Flow 
        if not is_test_function or len(block.control_flow_nodes) == 0: 
            continue
        
        # Ignore the Error Raise Block
        for next_block in block.next:
            if next_block.label == "<raise>": continue

        # Get the Line Number of the Block
        block_lines = extract_scope(block)
        
        # Block-Index
        block_index = min(block_lines)

        # Process the Block
        true_scope, false_scope, no_condition_lines = process_block_scopes(block)

        # Get the Next Block
        next_blocks = determine_next_blocks(block_range, true_scope, false_scope, no_condition_lines)
        next_block_dict[block_index] = next_blocks

    return next_block_dict

# Function 2 (Helper)
def process_block_scopes(block):
    true_scope = []
    false_scope = []
    no_condition_lines = []

    if block.branches:
        true_scope = extract_scope(block.branches[True])
        false_scope = extract_scope(block.branches[False])
    else:
        for next_block in block.next:
            no_condition_lines.extend(extract_scope(next_block))

    return true_scope, false_scope, no_condition_lines

# Function 2 (Helper)
def determine_next_blocks(block_range, true_scope, false_scope, no_condition_lines):
    result = {"with_condition": {"true": None, "false": None}, "no_condition": None}
    
    if true_scope:
        result["with_condition"]["true"] = find_scope_block(block_range, true_scope)
    if false_scope:
        result["with_condition"]["false"] = find_scope_block(block_range, false_scope)
    if not true_scope:
        result["with_condition"]["true"] = "<END>"
    if not false_scope:
        result["with_condition"]["false"] = "<END>"
    if no_condition_lines:
        result["no_condition"] = find_scope_block(block_range, no_condition_lines)
    
    return result

#  Function 2 (Helper)
def find_scope_block(block_range, scope_lines):
    min_line = min(scope_lines)
    max_line = max(scope_lines)
    for key, value in block_range.items():
        if value['range'] == [min_line, max_line]:
            return key
    return None

# Funtion 1 & 2 (Helper)
def extract_scope(block):
    scope = []
    for node in block.control_flow_nodes:
        instruction = node.instruction
        ast_node = instruction.node
        line_number = ast_node.lineno
        scope.append(line_number-1)
    return scope

# =======================================================

# Function 3
def renumbering_blocks(cfg_block_statements, cfg_block_range, cfg_next_block):
    # Renumber blocks from 1 to total_blocks

    # Renumber block_statements
    sorted_block_statements = {k: cfg_block_statements[k] for k in sorted(cfg_block_statements)}
    renumbering_dict = {old: new for new, old in enumerate(sorted_block_statements, start=1)}
    new_cfg_block_statements  = {renumbering_dict[k]: v for k, v in sorted_block_statements.items()}

    # Renumber block_range
    sorted_block_ranges = {k: cfg_block_range[k] for k in sorted(cfg_block_range)}
    new_cfg_block_ranges = {renumbering_dict[k]: v for k, v in sorted_block_ranges.items()}

    # Renumber next_block
    new_cfg_next_blocks = {}
    for old_block, connections in cfg_next_block.items():
        new_block = renumbering_dict[old_block]
        new_cfg_next_blocks[new_block] = {}
        for condition, next_blocks in connections.items():
            new_cfg_next_blocks[new_block][condition] = update_connection(condition, next_blocks, renumbering_dict)

    # Special Case to Handle the For Loop (iterator and iterate over in only one block)
    keys = list(new_cfg_block_statements.keys())[:-1]
    for key in keys:
        # Check if the next block has only one statement by checking the statement length
        block_length = len(new_cfg_block_statements[key+1])
        # Check if the next block has only one statement by checking block range
        block_start, block_end = new_cfg_block_ranges[key]['range']
        
        # Check if the current block's last statement is the same as the next block's first statement
        curr_block_last_statement = new_cfg_block_statements[key][-1]
        next_block_first_statement = new_cfg_block_statements[key + 1][0]
        # Check if the current block's last line and the next block's first line are same
        curr_block_last_line = new_cfg_block_ranges[key]['range'][1]
        next_block_first_line = new_cfg_block_ranges[key + 1]['range'][0]

        if block_length == 1 and block_start == block_end:
            if curr_block_last_statement == next_block_first_statement and curr_block_last_line == next_block_first_line:
                if 'iterator' in new_cfg_block_statements[key][-1] and 'iterator' in new_cfg_block_statements[key + 1][0]:
                    new_cfg_block_statements[key] = new_cfg_block_statements[key][:-1]
                    start_range, end_range = new_cfg_block_ranges[key]['range']
                    new_cfg_block_ranges[key]['range'] = [start_range, end_range - 1]

    return new_cfg_block_statements, new_cfg_block_ranges, new_cfg_next_blocks

# # Function 3 (Helper)
def update_connection(condition, next_blocks, renumbering_dict):
    if condition == "no_condition":
        if next_blocks == "<END>":
            return "<END>"
        return renumbering_dict.get(next_blocks, None)
    else:
        for _, next_block in next_blocks.items():
            if next_block == "<END>":
                return "<END>"
            elif next_block is not None:
                return renumbering_dict.get(next_block, None)
            else:
                return None

# =======================================================

# Function 4
def ground_truth_code_blocks_fixeval(cfg_block_range, execution_order, trace):
    ground_truth_blocks = []

    # Combine the execution order and the trace
    execution_order_trace_combined = []
    for index, line_number in enumerate(execution_order):
        try:
            line_number_in_trace = int(trace[index]['line'])
            if line_number_in_trace == int(line_number):
                var_val = trace[index]['var_val']
                execution_order_trace_combined.append({"line_number": line_number_in_trace, "state": var_val})
            else:
                execution_order_trace_combined.append({"line_number": int(line_number), "state": []})
        except Exception as e:
            execution_order_trace_combined.append({"line_number": int(line_number), "state": []})

    # Transform the execution order into the blocks
    ground_truth_code_blocks_range = {}
    for each_block in cfg_block_range:
        range = cfg_block_range[each_block]['range']
        min_line = range[0]; max_line = range[1]
        ground_truth_code_blocks_range[each_block] = [min_line, max_line]
    
    # Get the Execution Block Sequence
    last_block_added = None
    for entry in execution_order_trace_combined:
        line_number = entry['line_number']
        state = entry['state']
        for block_name, range_ in ground_truth_code_blocks_range.items():
            if range_[0] <= line_number <= range_[1]:
                if last_block_added == block_name: ground_truth_blocks[-1] = {"block" : block_name, "state" : state}
                if last_block_added != block_name:
                    ground_truth_blocks.append({"block" : block_name, "state" : state})
                    last_block_added = block_name
                break
            continue

    return ground_truth_blocks

# =======================================================

# Function 5
def cfg_to_text(block_statements, next_block_data, block_range):
    res = ""
    for block_index in block_range:
        res += f"\nBlock {block_index}:\n"
        range = block_range[block_index]["range"]
        min_range = range[0]
        max_range = range[1]
        total_lines = max_range - min_range + 1
        block_statement = block_statements[block_index]
        if len(block_statement) != total_lines: return ""
        res += "Statement:"
        for i in block_statement:
            res += f"\n    {i}"
        res += "\nNext:\n"
        try:
            next_block_statements_dict = next_block_data[block_index]
            true_next = next_block_statements_dict["with_condition"]["true"]
            false_next = next_block_statements_dict["with_condition"]["false"]
            no_condition_next = next_block_statements_dict["no_condition"]
            if true_next != None:
                if true_next == "<END>":    res += f"    <END>"
                else:   res += f"    If True: Go to Block {true_next}\n"
            if false_next != None:
                if false_next == "<END>":   res += f"    <END>"
                else:   res += f"    If False: Go to Block {false_next}\n"
            if true_next and false_next: continue
            else:
                if no_condition_next == "<END>":   res += f"    <END>\n"
                else:   res += f"    Go to Block: {no_condition_next}\n"
        except:
            res += f"    <END>\n"
    
    return res

# =======================================================