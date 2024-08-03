import os
import ast
import subprocess
from tqdm import tqdm

def write_code_to_test_function(file_path, submission_code):
    with open(file_path, 'w') as file:
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

def create_directory_if_not_exists(directory_path):
    """ Ensure the directory exists, create if it does not. """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def count_test_cases_in_directory(directory_path):
    """ Count files in the directory that match the 'input_' prefix. """
    return sum(1 for file in os.listdir(directory_path) if file.startswith('input_'))

def main(folder_apth, dataset):
    example_file_path = folder_apth / 'example.py'
    output_path = folder_apth / 'output'
    create_directory_if_not_exists(output_path)
    cache_folder_path = output_path / 'TraceFiles'
    base_test_case_path = folder_apth / 'TestCases'
    hunter_tool_path = folder_apth / 'hunter_tool.py'
    # Make sure the output directory exists with the TraceFiles folder
    create_directory_if_not_exists(cache_folder_path)

    # Iterate through the dataset
    for problemID in tqdm(dataset):
        # Skip processing if no test cases are found or if already processed
        testcase_path = f"{base_test_case_path}/{problemID}"
        output_directory = f'{cache_folder_path}/{problemID}/'
        if not os.path.exists(testcase_path) or os.path.exists(output_directory):
            continue

        create_directory_if_not_exists(f'{cache_folder_path}/{problemID}/')
        
        # Count the number of test cases for the problem
        testCase_count = count_test_cases_in_directory(testcase_path)
        if testCase_count == 0:
            continue
        
        for index, sub_ID in enumerate(dataset[problemID]):

            output_path = f"{output_directory}{sub_ID}"
            
            # Write the code to a file for execution
            code = dataset[problemID][sub_ID]['code']
            write_code_to_test_function(example_file_path, code)

        
            # Execute Hunter tool with the first test case
            test_case_file_path = f"{testcase_path}/input_1.txt"
            output_file_path = f"{output_path}_1.txt"
            with open(test_case_file_path, 'r') as test_case_file, open(output_file_path, 'w') as output_file:
                try:
                    variables_in_the_code = get_variable_names(code)
                    env = os.environ.copy()
                    env['HUNTER_TRACE_VARS'] = ','.join(variables_in_the_code)
                    subprocess.run(['python', str(hunter_tool_path)], stdin=test_case_file, stdout=output_file, stderr=subprocess.STDOUT, timeout=10, env=env)
                except Exception as e:
                    continue

def get_execution_trace(folder_apth, dataset):
    main(folder_apth, dataset)