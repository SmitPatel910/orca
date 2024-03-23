import json
import os
from tqdm import tqdm
import subprocess
import ast
import hunter

with open('../../dataset/filtered_fixeval_dataset.json', 'r') as file:
    fixeval_dataset = json.load(file)

def write_code_to_test_function(submission_code):
    with open('example.py', 'w') as file:
        file.write("def test_function():\n")
        lines = submission_code.split('\n')
        line_index = 0
        while line_index < len(lines):
            current_line = lines[line_index]
            file.write("    " + current_line + "\n")
            line_index += 1

class VariableNameCollector(ast.NodeVisitor):
    def __init__(self):
        self.names = set()

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, (ast.Tuple, ast.List)):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.names.add(elt.id)
            elif isinstance(target, ast.Name):
                self.names.add(target.id)
        # Continue visiting children nodes
        self.generic_visit(node)

def get_variable_names(code):
    tree = ast.parse(code)
    collector = VariableNameCollector()
    collector.visit(tree)
    vars = collector.names
    variables_to_trace = list(vars)
    return variables_to_trace

prob_count = 0
sub_count = 0
false_count = 0
true_count = 0
# iterate through the dataset
for problemID in tqdm(fixeval_dataset):
    prob_count += 1

    traceDict = {}
    if os.path.exists(f'output/TraceFiles/{problemID}/'):   continue
    else: os.makedirs(f'output/TraceFiles/{problemID}/')
    
    for index, submissionCode in enumerate(fixeval_dataset[problemID]):
        sub_count += 1
        output_path = f"output/TraceFiles_2/{problemID}/{submissionCode}"
        if not os.path.exists(f"TestCases/{problemID}"): continue
        
        code = fixeval_dataset[problemID][submissionCode]['code']
        write_code_to_test_function(code)

        testCase_count = 0
        testcase_path = f"TestCases/{problemID}"
        for file in os.listdir(testcase_path):
            if file.startswith('input_'):   testCase_count += 1
        hunter_output = None
        if testCase_count == 0: continue

        with open(f"{testcase_path}/input_{1}.txt", 'r') as test_case_file, open(f"{output_path}_1.txt", 'w') as output_file:
            try:
                variables_to_trace = get_variable_names(code)
                env = os.environ.copy()
                env['HUNTER_TRACE_VARS'] = ','.join(variables_to_trace)
                subprocess.run(['python','hunter_tool.py'], stdin=test_case_file, stdout=output_file, stderr=subprocess.STDOUT, timeout=10, env = env)
                true_count += 1
            except:
                false_count += 1
                continue

print(f"Total: {sub_count}, True: {true_count}, False: {false_count}")
