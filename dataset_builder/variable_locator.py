import ast
import json
from tqdm import tqdm

class InputVisitor(ast.NodeVisitor):
    def __init__(self):
        self.input_vars = []
        self.append_inputs = []
        self.return_inputs = []

    def visit_Lambda(self, node):
        self.lambda_functions.append(node)
        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.value, (ast.Tuple, ast.Call, ast.ListComp, ast.GeneratorExp)):
            values_to_check = [node.value] if not isinstance(node.value, ast.Tuple) else node.value.elts
            if any(self.contains_input_call(value) for value in values_to_check):
                for target in node.targets:
                    if isinstance(target, ast.Tuple):
                        for elt in target.elts:
                            if isinstance(elt, ast.Name):
                                self.input_vars.append((elt.id, node.lineno))
                    elif isinstance(target, ast.Name):
                        self.input_vars.append((target.id, node.lineno))
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'append':
            if isinstance(node.args[0], ast.Call) and self.contains_input_call(node.args[0]):
                self.append_inputs.append((node.func.value.id, node.lineno))
        self.generic_visit(node)

    def contains_input_call(self, node):
        if isinstance(node, ast.Call):
            if getattr(node.func, 'id', '') == 'input':
                return True
        elif isinstance(node, ast.ListComp):
            return self.contains_input_call(node.elt) or any(self.contains_input_call(gen.iter) for gen in node.generators)
        for child_node in ast.iter_child_nodes(node):
            if self.contains_input_call(child_node):
                return True
        return False
    
    def visit_Return(self, node):
        if isinstance(node.value, ast.Call) and self.contains_input_call(node.value):
            self.return_inputs.append(("return_statement", node.lineno))
        self.generic_visit(node)

    def report(self):
        return self.input_vars, self.append_inputs, self.return_inputs

def find_input_variables_from_file(code):
    tree = ast.parse(code)
    visitor = InputVisitor()
    visitor.visit(tree)
    return visitor.report()

# Check if there is any while loop
class WhileLoopFinder(ast.NodeVisitor):
    def __init__(self):
        self.while_loops = []

    def visit_While(self, node):
        start_line = node.lineno
        end_line = max(child.lineno for child in ast.walk(node) if hasattr(child, 'lineno'))
        self.while_loops.append((start_line, end_line))
        self.generic_visit(node)

def find_while_loops(code):
    tree = ast.parse(code)
    finder = WhileLoopFinder()
    finder.visit(tree)
    return finder.while_loops

# Check if there is any For loop
class ForLoopFinder(ast.NodeVisitor):
    def __init__(self):
        self.for_loop_scope_2 = []
        self.for_loop_scopes = []
    def visit_For(self, node):
        start_line = node.lineno
        end_line = max(child.lineno for child in ast.walk(node) if hasattr(child, 'lineno'))

        loop_scope = (start_line, end_line)
        if end_line - start_line == 1:
            self.for_loop_scope_2.append(loop_scope)
        else:
            self.for_loop_scopes.append(loop_scope)

        self.generic_visit(node)

def find_for_loops(code):
    tree = ast.parse(code)
    finder = ForLoopFinder()
    finder.visit(tree)
    return finder.for_loop_scope_2, finder.for_loop_scopes

def if_else_in_same_line(code):
    lines = code.split('\n')
    for line in lines:
        if 'if' in line and 'else' in line:
            return True

    return False

def caller_function(codeDict):
    error_count = 0
    variables_in_while_loop = 0
    variables_in_for_loop = 0
    variables_on_last_line_of_for_loop_scope_2 = 0
    variables_in_methods = 0

    variable_location = {}

    prob_count = 0
    sub_count = 0   
    print("Total problems: ", len(codeDict))
    for problemID in tqdm(codeDict):
        prob_count += 1
        submissions = {}
        for submissionCode in codeDict[problemID].keys():
            sub_count += 1
            
            code = codeDict[problemID][submissionCode]['code']
            temp_dict = {}
            is_while_loop = False
            is_for_loop_scope_2 = False
            is_for_loop = False
            is_method = False
            try:
                # Inputs from different sources
                assigned_vars, append_inputs, return_inputs = find_input_variables_from_file(code)
                input_variables = assigned_vars + append_inputs + return_inputs

                while_loops = find_while_loops(code)
                # While Loop // check the input variables from the while loop
                for var, line in input_variables:
                    if any(start <= line <= end for start, end in while_loops):
                        is_while_loop = True
                        variables_in_while_loop += 1
                # For Loop // check the input variables from the for loop
                for_loop_scope_2, for_loop_scope_more_than_2 = find_for_loops(code)
                for var, line in input_variables:
                    if any(line == end_line for _, end_line in for_loop_scope_2):
                        variables_on_last_line_of_for_loop_scope_2 += 1
                        is_for_loop_scope_2 = True
                    elif any(line == end_line for _, end_line in for_loop_scope_more_than_2):
                        variables_in_for_loop += 1
                        is_for_loop = True
                # Inputs in the return statement
                if len(return_inputs) != 0:
                    variables_in_methods += 1
                    is_method = True
                temp_dict = {'code': code, 'Input variables': input_variables, 'if_else_same_line': if_else_in_same_line(code) , 'while_loop': is_while_loop, 'for_loop_scope_2': is_for_loop_scope_2, 'for_loop': is_for_loop, 'method': is_method}
            except Exception as e:
                error_count += 1

            submissions[submissionCode] = temp_dict

        variable_location[problemID] = submissions

    return variable_location
