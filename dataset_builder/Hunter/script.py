import os
import ast
import subprocess
from tqdm import tqdm

def write_code_to_test_function(file_path, submission_code):
    '''Write submission code into a file as a `test_function`.

    This function takes a block of submission code, formats it into a `test_function`,
    and writes it into a specified file. Each line of the submission code is indented
    to fit inside the function definition.

    Args:
        file_path (str): The path of the file where the `test_function` will be written.
        submission_code (str): The source code to be wrapped inside the `test_function`.

    Returns:
        None
    '''
    with open(file_path, 'w') as file:
        file.write("def test_function():\n")
        lines = submission_code.split('\n')
        line_index = 0
        while line_index < len(lines):
            current_line = lines[line_index]
            file.write("    " + current_line + "\n")
            line_index += 1

class VariableNameCollector(ast.NodeVisitor):
    '''Collect variable names from assignment statements in Python code.

    This class extends `ast.NodeVisitor` to traverse an abstract syntax tree (AST)
    and collect variable names found in assignment statements. It handles both
    simple variable assignments and unpacking assignments (e.g., tuples or lists).

    Attributes:
        names (set): A set containing all collected variable names.

    Methods:
        visit_Assign(node): Visit assignment nodes and extract variable names.
    '''
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
    '''Extract all variable names from the given Python source code.

    This function parses the provided Python code into an abstract syntax tree (AST),
    uses the `VariableNameCollector` class to visit the tree, and collects all variable
    names found in assignment statements.

    Args:
        code (str): The Python source code as a string.

    Returns:
        list: A list of unique variable names found in the code.
    '''
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
    '''Process a dataset of code submissions to generate execution traces using the Hunter tool.

    This function iterates through a dataset of problems and their submissions, executes 
    each submission with the corresponding test cases, and stores the execution traces 
    for analysis. It ensures necessary directories are created, writes the code to a file, 
    and runs the Hunter tool to trace variable execution.

    Args:
        folder_path (Path): The base folder path containing required directories and files:
            - `example.py`: File where code submissions are written for execution.
            - `output`: Directory where execution traces are stored.
            - `TestCases`: Directory containing test cases for each problem.
            - `hunter_tool.py`: Script for tracing variable executions.
        dataset (dict): The dataset of problems and submissions, structured as:
           
    Returns:
        None
        
    Notes:
        - Skips problems without test cases or already processed outputs.
        - Uses environment variables to pass variable names for tracing.
        - Execution is limited to 10 seconds per submission.
    '''

    # Set up paths for required files and directories
    example_file_path = folder_apth / 'example.py'
    output_path = folder_apth / 'output'
    create_directory_if_not_exists(output_path)
    cache_folder_path = output_path / 'TraceFiles'
    base_test_case_path = folder_apth / 'TestCases'
    hunter_tool_path = folder_apth / 'hunter_tool.py'
    # Make sure the output directory exists with the TraceFiles folder
    create_directory_if_not_exists(cache_folder_path)


    # Iterate over each problem in the dataset
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
            continue  # Skip if no test cases found
        
        # Process each submission for the problem
        for index, sub_ID in enumerate(dataset[problemID]):
            # Set up output path for the submission
            output_path = f"{output_directory}{sub_ID}"
            
            # Write the submission code to `example.py`
            code = dataset[problemID][sub_ID]['code']
            write_code_to_test_function(example_file_path, code)

            # Execute Hunter tool with the first test case
            test_case_file_path = f"{testcase_path}/input_1.txt"
            output_file_path = f"{output_path}_1.txt"
            with open(test_case_file_path, 'r') as test_case_file, open(output_file_path, 'w') as output_file:
                try:
                    # Extract variable names from the submission code
                    variables_in_the_code = get_variable_names(code)
                    # Set up environment variables for the Hunter tool
                    env = os.environ.copy()
                    env['HUNTER_TRACE_VARS'] = ','.join(variables_in_the_code)
                    # Run the Hunter tool with the test case
                    subprocess.run(
                        ['python', str(hunter_tool_path)], 
                        stdin=test_case_file, 
                        stdout=output_file, 
                        stderr=subprocess.STDOUT, 
                        timeout=10, # Limit execution time to 10 seconds
                        env=env
                    )
                except Exception as e:
                    continue

def get_execution_trace(folder_apth, dataset):
    main(folder_apth, dataset)