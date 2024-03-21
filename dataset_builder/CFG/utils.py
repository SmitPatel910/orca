import ast
import json
 
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
 
def adjust_block_indentation(code):
    lines = code.split('\n')
    first_line_indent = None
    for line in lines:
        if line.strip():
            first_line_indent = len(line) - len(line.lstrip())
            break
    
    if first_line_indent is None:
        return code
    adjusted_lines = []
    for line in lines:
        if line.strip():
            adjusted_line = line[first_line_indent:]
            adjusted_lines.append(adjusted_line)
        else:
            adjusted_lines.append(line)
    adjusted_code = '\n'.join(adjusted_lines)
    return adjusted_code
 
# def check_next_line(code, start, end):
#     length = len(code.split('\n'))
#     # Length of the code and the end scope is same
#     if end+1 >= length: return code.split('\n')[start:end+1], start, end
#     line = code.split('\n')[end+1]
#     # If the next line is a 'if' statement
#     # if 'if' in line:
#     #     # If the next line from the for loop is IF statement and there is no next statement: e.g. if ans: print(ans)
#     #     if end+2 >= length: return code.split('\n')[start:end+2], start, end+1
#     #     # If the next line from the for loop is IF statement and there is a next statement.
#     #     else: return code.split('\n')[start:end+3], start, end+2
#     if 'if' in line or 'return' in line or 'break' in line or 'continue' in line:
#         return code.split('\n')[start:end+1], start, end
#     else:
#         return code.split('\n')[start:end+2], start, end+1
 
# def extract_for_loop(code, start,end):
#     list_lines, updated_start, updated_end = check_next_line(code, start, end)
#     fcode = '\n'.join(list_lines)
#     final_code = adjust_block_indentation(fcode)
#     return final_code, updated_start, updated_end
 
# def safe_eval_list(value):
#     if value.startswith("[") and value.endswith("]"):
#         return value.strip("[] ").split(" , ")
#     if value == "['']": return []
#     return value

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
    except Exception as e:
        print(f"Error: {e}")
        print(source_code)

def extract_statements_range_from_block(cfg, code, for_loop_code):
    block_range = {}; block_statement = {}; flag = False
 
    for block in cfg.blocks:
        # Ignore the block which has function defination of the template code
        if block.label == "<entry:testFun>": flag = True
        if not flag: continue
        # Ignore the Block with No Control Flow
        if len(block.control_flow_nodes) == 0 : continue
        # Ignore the Last Block
        for next_block in block.next:
            if next_block.label == "<raise>": continue
        # block_index += 1
        line_number_list = []
        for node in block.control_flow_nodes:
            instruction = node.instruction
            ast_node = instruction.node
            line_number = ast_node.lineno
            line_number_list.append(line_number-1)
        # Block-Range
        block_index = min(line_number_list)
        block_range[block_index] = {"range": [min(line_number_list), max(line_number_list)]}
        # Block-Statement
        statements = []
        for number in line_number_list:
            statements.append(statement_transformation(for_loop_code, number))
        block_statement[block_index] = statements
    # print("Modified Block Range: ", block_range)
    # print("Modified Block Statement: ", block_statement)
    return block_range, block_statement

def get_the_next_block(block_range, cfg):
    next_block_dict = {}; flag = False
    for block in cfg.blocks:
        true_scope_block = []; false_scope_block = []; no_condition_block_lines = []; true_next = None; false_next = None; no_condition_next = None
        # Ignore the block which has function defination of the template code
        if block.label == "<entry:testFun>": flag = True
        if not flag: continue
        # Ignore the Block with No Control Flow
        if len(block.control_flow_nodes) == 0 : continue
        # Ignore the Last Block
        for next_block in block.next:
            if next_block.label == "<raise>": continue
        # Filtered Block
        line_number_list = []
        for node in block.control_flow_nodes:
            instruction = node.instruction
            ast_node = instruction.node
            line_number = ast_node.lineno
            line_number_list.append(line_number-1)
        block_index = min(line_number_list)

        if block.branches:
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
        else:
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
            for key, value in block_range.items():
                if value['range'] == [min_line_number, max_line_number]:
                    true_next = key
                    break
            # False Scope
            min_line_number = min(false_scope_block)
            max_line_number = max(false_scope_block)
            for key, value in block_range.items():
                if value['range'] == [min_line_number, max_line_number]:
                    false_next = key
                    break
        elif true_scope_block:
            # Block with True Scope
            min_line_number = min(true_scope_block)
            max_line_number = max(true_scope_block)
            for key, value in block_range.items():
                if value['range'] == [min_line_number, max_line_number]:
                    true_next = key
                    false_next = "<END>"
                    break
        elif false_scope_block:
            # Block with False Scope
            min_line_number = min(false_scope_block)
            max_line_number = max(false_scope_block)
            for key, value in block_range.items():
                if value['range'] == [min_line_number, max_line_number]:
                    true_next = "<END>"
                    false_next = key
                    break
        else:
            # Block with No Condition
            if not no_condition_block_lines: continue
            min_line_number = min(no_condition_block_lines)
            max_line_number = max(no_condition_block_lines)
            for key, value in block_range.items():
                if value['range'] == [min_line_number, max_line_number]:
                    no_condition_next = key
                    break
        next_block_dict[block_index] = {
            "with_condition": {"true": true_next, "false": false_next} ,  
            "no_condition": no_condition_next
        }
 
    return next_block_dict
    
# def extract_relavent_information(code, ground_truth_trace):
#     temp_ground_truth = []
#     for line in ground_truth_trace:
#         parts = line.split("<state>")
#         line_number = int(parts[0].split()[1].strip("<>"))
#         state_content = parts[1].replace("</state>", "").strip()
#         state_dict = {}
#         for part in state_content.split(" <dictsep> "):
#             split_part = part.split(" : ")
#             if len(split_part) == 2:
#                 key, value = split_part
#                 state_dict[key] = safe_eval_list(value)
#             else:
#                 key = split_part[0]
#                 state_dict[key] = ""
#         temp_ground_truth.append({"line_number": line_number, "state": state_dict})
 
#     cfg_nodes = ['continue', 'break', 'return', 'try', 'except']
#     # Get the line number of the nodes in the code
#     line_number_to_node = []
#     for index, line in enumerate(code.split('\n')):
#         for node in cfg_nodes:
#             if 'if' in line and node in line: continue
#             if node in line:
#                 line_number_to_node.append(index)
#     # Remove the nodes from the ground truth
#     final_ground_truth = []
#     for item in temp_ground_truth:
#         line_number = item['line_number']
#         if line_number in line_number_to_node:
#             continue
#         else:
#             final_ground_truth.append(item)
 
#     return final_ground_truth
 
# def extract_gt_for_loop(id, code, ground_truth, start, end):
#     ground_truth_trace = []
#     for line in ground_truth:
#         if not "<line> <" in line and "<output>" not in line: continue
#         if not line.startswith("<line>"): continue
#         line_number = int(line.split()[1].strip("<>"))
#         if start <= line_number <= end:
#             ground_truth_trace.append(line)
#     final_ground_truth = extract_relavent_information(code, ground_truth_trace)
#     return final_ground_truth
 
def ground_truth_blocks(cfg_block_range, for_loop_ground_truth):
    # Ground Truth Execution Trace
    ground_truth_block_execution_order = []
    diff = for_loop_ground_truth[0]['line_number'] - 1 # First line of the for loop
 
    ground_truth_code_blocks_range = {}
    for each_block in cfg_block_range:
        range = cfg_block_range[each_block]['range']
        min_line = range[0]; max_line = range[1]
        ground_truth_code_blocks_range[each_block] = [min_line + diff, max_line + diff]
 
    # Get the Execution Block Sequence
    last_block_added = None
    for entry in for_loop_ground_truth:
        line_number = entry['line_number']
        state = entry['state']
        for block_name, range_ in ground_truth_code_blocks_range.items():
            if range_[0] <= line_number <= range_[1]:
                if last_block_added == block_name: ground_truth_block_execution_order[-1] = {"block" : block_name, "state" : state}
                if last_block_added != block_name:
                    ground_truth_block_execution_order.append({"block" : block_name, "state" : state})
                    last_block_added = block_name
                break
            continue
    return ground_truth_block_execution_order, diff

def renumbering_blocks(cfg_block_statements, cfg_block_range, cfg_next_block):
    # Renumber block_statements
    sorted_block_statements = {k: cfg_block_statements[k] for k in sorted(cfg_block_statements)}
    # Renumber blocks from 1 to total_blocks
    renumbering_dict = {old: new for new, old in enumerate(sorted_block_statements, start=1)}
    renumbered_statements = {renumbering_dict[k]: v for k, v in sorted_block_statements.items()}

    # Renumber block_range
    sorted_block_ranges = {k: cfg_block_range[k] for k in sorted(cfg_block_range)}
    renumbered_ranges = {renumbering_dict[k]: v for k, v in sorted_block_ranges.items()}

    # Renumber next_block
    renumbered_connections_corrected = {}
    for old_block, connections in cfg_next_block.items():
        new_block = renumbering_dict[old_block]
        renumbered_connections_corrected[new_block] = {}
        for condition, next_blocks in connections.items():
            if condition == "no_condition":
                if next_blocks == "<END>":
                    renumbered_connections_corrected[new_block][condition] = "<END>"
                renumbered_connections_corrected[new_block][condition] = renumbering_dict.get(next_blocks, None)
            else:
                renumbered_connections_corrected[new_block][condition] = {}
                for true_false, next_block in next_blocks.items():
                    if next_block == "<END>":
                        renumbered_connections_corrected[new_block][condition][true_false] = "<END>"
                    elif next_block is not None:
                        renumbered_connections_corrected[new_block][condition][true_false] = renumbering_dict.get(next_block, None)
                    else:
                        renumbered_connections_corrected[new_block][condition][true_false] = None

    keys = list(renumbered_statements.keys())[:-1]
    for key in keys:
        if len(renumbered_statements[key + 1]) == 1 and renumbered_ranges[key + 1]['range'][0] == renumbered_ranges[key + 1]['range'][1]:
            if renumbered_statements[key][-1] == renumbered_statements[key + 1][0] and renumbered_ranges[key]['range'][1] == renumbered_ranges[key + 1]['range'][0]:
                if 'iterator' in renumbered_statements[key][-1] and 'iterator' in renumbered_statements[key + 1][0]:
                    renumbered_statements[key] = renumbered_statements[key][:-1]
                    start_range, end_range = renumbered_ranges[key]['range']
                    renumbered_ranges[key]['range'] = [start_range, end_range - 1]

    return renumbered_statements, renumbered_ranges, renumbered_connections_corrected

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


def make_cfg_into_code(block_statements, next_block_data, block_range):
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