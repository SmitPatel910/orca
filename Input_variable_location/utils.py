import ast
import re
from tqdm import tqdm

class CodeAnalyzer(ast.NodeVisitor):
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
    tree = ast.parse(code)
    analyzer = CodeAnalyzer()
    analyzer.visit(tree)
    return analyzer

def check_code_conditions(analyzer):
    if analyzer.method_count > 0: return False
    if analyzer.for_count != 0 and analyzer.while_count!= 0: return False
    if analyzer.for_count > 1: return False
    if analyzer.while_count > 1: return False
    return True

def remove_comments_and_blank_lines(code):
    code = re.sub(r'#.*', '', code)
    code = re.sub(r"'''(.*?)'''", '', code, flags=re.DOTALL)
    code = re.sub(r'"""(.*?)"""', '', code, flags=re.DOTALL)
    lines = code.split('\n')
    clean_lines = [line for line in lines if line.strip() != '']
    code = '\n'.join(clean_lines)
    return code

def filter_code_based_on_input_lines(dataset):
    filter_dataset = {}
    true_count = 0
    for key in tqdm(dataset.keys()): # key: problem_id
        if key not in dataset:
            filter_dataset[key] = {}
        temp = {}
        for submission in dataset[key]: # submission: submission_id
            submission_block = dataset[key][submission] # submission_block: submission block
            if not submission_block: continue
            # Filter out the submissions based on: input variables inside the if_else_same_line, while_loop, for_loop_scope_2, for_loop, method
            if submission_block["if_else_same_line"] or submission_block["while_loop"] or submission_block["for_loop_scope_2"] or submission_block["for_loop"] or submission_block["method"]: continue
            input_var = submission_block['Input variables']
            if input_var == []: continue
            true_count += 1
            temp[submission] = dataset[key][submission]
        filter_dataset[key] = temp
    return filter_dataset

