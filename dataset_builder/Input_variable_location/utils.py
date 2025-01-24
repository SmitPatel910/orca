import ast
import re
from tqdm import tqdm

class CodeAnalyzer(ast.NodeVisitor):
    '''AST NodeVisitor to analyze the structure of Python code and count specific constructs.

    This class traverses the abstract syntax tree (AST) of Python code and counts:
    - `for` loops
    - `while` loops
    - Method (function) definitions

    Attributes:
        for_count (int): Number of `for` loops found in the code.
        while_count (int): Number of `while` loops found in the code.
        method_count (int): Number of function definitions found in the code.

    Methods:
        visit_For(node): Increments the `for_count` when a `for` loop is encountered.
        visit_While(node): Increments the `while_count` when a `while` loop is encountered.
        visit_FunctionDef(node): Increments the `method_count` when a function definition is encountered.
    '''
    def __init__(self):
        self.for_count = 0
        self.while_count = 0
        self.method_count = 0

    def visit_For(self, node):
        self.for_count += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.while_count += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.method_count += 1
        self.generic_visit(node)

def analyze_code(code):
    '''Analyze Python code to count occurrences of loops and method definitions.

    This function parses the provided Python code into an abstract syntax tree (AST),
    traverses the tree using the `CodeAnalyzer` class, and counts:
    - Number of `for` loops
    - Number of `while` loops
    - Number of function definitions

    Args:
        code (str): The Python source code to analyze.

    Returns:
        CodeAnalyzer: An instance of the `CodeAnalyzer` class containing the counts of `for` loops,
                      `while` loops, and method definitions.
    '''
    tree = ast.parse(code)
    analyzer = CodeAnalyzer()
    analyzer.visit(tree)
    return analyzer

def check_code_conditions(analyzer):
    # Control Flow Graph can not generate full complete graph for the code with multiple functions, 
    # hence we are not considering the code with multiple functions. (This is not the limitation of ORCA)
    if analyzer.method_count > 0: return False

    # Check if there are multiple for loops or while loops
    if analyzer.for_count != 0 and analyzer.while_count!= 0: return False

    # Check if there are multiple for loops or while loops
    if analyzer.for_count > 1: return False
    
    # Check if there are multiple while loops
    if analyzer.while_count > 1: return False
    
    return True

def remove_comments_and_blank_lines(code):
    '''Remove comments and blank lines from the code.'''
    code = re.sub(r'#.*', '', code)
    code = re.sub(r"'''(.*?)'''", '', code, flags=re.DOTALL)
    code = re.sub(r'"""(.*?)"""', '', code, flags=re.DOTALL)
    lines = code.split('\n')
    clean_lines = [line for line in lines if line.strip() != '']
    code = '\n'.join(clean_lines)
    return code

def filter_code_based_on_input_lines(dataset):
    '''Filter a dataset based on input variable usage and code structure conditions.

    This function processes a dataset of code submissions and filters out submissions 
    that meet specific structural or variable usage conditions. Submissions are excluded if:
    - Input variables appear in certain constructs:
        - `if_else_same_line`
        - `while_loop`
        - `for_loop_scope_2` (last line of a for loop with scope size 2)
        - `for_loop`
        - `multiple method definitions` in the code
    
    Args:
        dataset (dict): A dataset containing problems and their submissions.
    
    Returns:
        dict: A filtered dataset excluding submissions that meet the above conditions.
    '''
    filter_dataset = {}
    true_count = 0
    for key in tqdm(dataset.keys()): # key: problem_id
        if key not in dataset:
            filter_dataset[key] = {}
        temp = {}
        for submission in dataset[key]:
            submission_block = dataset[key][submission]
            if not submission_block: continue
            # Filter out the submissions based on: 
            # input variables inside the if_else_same_line, while_loop, for_loop_scope_2, for_loop, method count
            if submission_block["if_else_same_line"] or \
                submission_block["while_loop"] or submission_block["for_loop_scope_2"] or \
                submission_block["for_loop"] or submission_block["method"]: 
                continue
            input_var = submission_block['Input variables']
            if input_var == []: continue
            true_count += 1
            temp[submission] = dataset[key][submission]
        filter_dataset[key] = temp
    return filter_dataset
