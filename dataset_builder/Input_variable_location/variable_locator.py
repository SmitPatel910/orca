import ast
from tqdm import tqdm

class InputVisitor(ast.NodeVisitor):
    '''AST NodeVisitor to identify and collect input-related variables and operations.

    This class traverses an abstract syntax tree (AST) of Python code and extracts:
    - Variables assigned from input operations.
    - Variables that append results of input operations to lists.
    - Return statements involving input operations.

    Attributes:
        input_vars (list): A list of variables assigned using input calls, with their line numbers.
        append_inputs (list): A list of variables to which input call results are appended, with their line numbers.
        return_inputs (list): A list of return statements containing input calls, with their line numbers.
    '''
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
    '''Parse Python code to identify variables and operations related to input calls.

    This function uses the `InputVisitor` class to traverse the abstract syntax tree (AST)
    of the provided Python code and extract:
    - Variables assigned using input calls.
    - List operations that append results of input calls.
    - Return statements containing input calls.

    Args:
        code (str): The Python source code as a string.

    Returns:
        tuple: A tuple containing:
            - input_vars (list): Variables assigned using input calls with line numbers.
            - append_inputs (list): Variables to which input call results are appended with line numbers.
            - return_inputs (list): Return statements involving input calls with line numbers.
    '''
    tree = ast.parse(code)
    visitor = InputVisitor()
    visitor.visit(tree)
    return visitor.report()

# Check If Code has any while loop
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

# Check If Code has any For loop
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

# Check If Code has if else in the same line
def if_else_in_same_line(code):
    lines = code.split('\n')
    for line in lines:
        if 'if' in line and 'else' in line:
            return True

    return False

def main(codeDict):
    '''Analyze a dataset of code submissions to identify and classify input variable usage.

    This function processes a dataset of code submissions, analyzing each submission for the following:
    - Input variables assigned, appended, or returned.
    - Input variables used in while loops, for loops (of different scope sizes), and methods.
    - Input variables on the last line of for loop scopes with specific conditions.
    - Presence of if-else statements on the same line.

    We are flagging those submissions that contain input variables in above mentioned conditions to 
    choose good quality submissions for the dataset and make the Control Flow Graphs more accurate.

    Args:
        codeDict (dict): A dictionary containing problems and their submissions.

    Returns:
        dict: A dictionary mapping each problem ID and submission ID to its analyzed results.

    Key Variables:
        - variables_in_while_loop (int): Count of instances has input in while loops.
        - variables_in_for_loop (int): Count of instances has input in for loops.
        - variables_on_last_line_of_for_loop_scope_2 (int): Count of instances has input on the last line of for loop scope 2.
        - variables_in_methods (int): Count of instances has input in the return statement.
    '''

    error_count = 0
    variables_in_while_loop = 0
    variables_in_for_loop = 0
    variables_on_last_line_of_for_loop_scope_2 = 0
    variables_in_methods = 0

    variable_location = {}

    prob_count = 0
    sub_count = 0   

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

