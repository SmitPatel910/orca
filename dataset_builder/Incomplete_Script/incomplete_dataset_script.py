import json
import random
import ast

class ImportRemover(ast.NodeTransformer):
    '''Custom AST Node Transformer to remove import statements from Python code.

    This class traverses the abstract syntax tree (AST) of a Python script and removes
    all `import` and `from ... import ...` statements. It also keeps track of the line numbers 
    where imports were removed.

    Attributes:
        removed_lines (list): A list of line numbers where imports were removed.
    '''
    def __init__(self):
        super().__init__()
        self.removed_lines = []

    def visit_Import(self, node):
        # Remove `import` statements and record their line numbers.
        self.removed_lines.append(node.lineno)
        return None

    def visit_ImportFrom(self, node):
        # Remove `from ... import ...` statements and record their line numbers.
        self.removed_lines.append(node.lineno)
        return None

def remove_imports(code):
    '''Remove all import statements from Python code and return the modified code.

    This function parses the given Python code into an abstract syntax tree (AST),
    removes all `import` and `from ... import ...` statements, and returns the modified 
    code along with the line numbers of the removed imports.

    Args:
        code (str): The input Python code as a string.

    Returns:
        tuple:
            - new_code (str): The modified code with import statements removed.
            - removed_lines (list): A list of line numbers where imports were removed.
    '''
    tree = ast.parse(code)
    remover = ImportRemover()
    new_tree = remover.visit(tree)
    new_code = ast.unparse(new_tree)
    return new_code, remover.removed_lines

def remove_imports_and_blank_lines(code):
    '''Removes import statements and blank lines from the code'''
    lines = [line for line in code.split('\n') if not (line.strip().startswith('import ') or line.strip().startswith('from '))]
    return '\n'.join(lines)

def select_instances(prob_count_list, total_count):
    '''Select a fixed number of instances from a list of problems, ensuring balanced distribution.

    This function distributes a specified total number of instances (`total_count`) 
    across a list of problems, ensuring each problem gets a fair share. If there are 
    leftover instances after even distribution, they are randomly allocated.

    Args:
        prob_count_list (list): A list of tuples where each tuple contains:
            - prob (str): The problem ID.
            - count (int): The number of available instances for the problem.
        total_count (int): The total number of instances to select across all problems.

    Returns:
        dict: A mapping of problem IDs to the number of selected instances.
    '''
    selected_instances = []

    # Calculate the number of instances to select per problem
    instances_per_category = total_count // len(prob_count_list)
    
    # Distribute instances evenly across all problems
    for prob, count in prob_count_list:
        selected_instances.extend([prob] * min(instances_per_category, count))
    
    # Calculate the number of remaining instances
    remaining_count = total_count - len(selected_instances)
    
    if remaining_count > 0:
        # Collect remaining instances from problems with extra capacity
        remaining_instances = []
        for prob, count in prob_count_list:
            # Add only the excess instances beyond the evenly allocated ones
            remaining_instances.extend([prob] * max(0, count - instances_per_category))
        
        # Randomly shuffle the remaining instances to ensure fairness
        random.shuffle(remaining_instances)
        # Add enough remaining instances to reach the total count
        selected_instances.extend(remaining_instances[:remaining_count])
    
    # Create a mapping of problem IDs to the number of selected instances
    instance_map = {}
    for prob in selected_instances:
        if prob not in instance_map:
            instance_map[prob] = 0
        instance_map[prob] += 1

    return instance_map

def select_sub_data(dataset, instance_map, prob_sub_mapping):
    '''Select a subset of submissions for each problem based on instance mapping.

    This function extracts a specified number of submissions for each problem from the dataset, 
    shuffling the available submissions for randomness before selection.

    Args:
        dataset (dict): The full dataset containing problems and their submissions.
        instance_map (dict): A mapping of problem IDs to the number of submissions to select.
        prob_sub_mapping (dict): A mapping of problem IDs to a list of their available submission IDs.

    Returns:
        dict: A subset of the dataset containing only the selected submissions.
    '''
    selected_data = {}
    for prob, count in instance_map.items():
        selected_data[prob] = {}
        available_subs = prob_sub_mapping[prob]
        random.shuffle(available_subs)
        temp = {}
        for sub in available_subs[:count]:
            temp[sub] = dataset[prob][sub]
        selected_data[prob] = temp
    return selected_data

def load_datasets():
    with open("fixeval_crash_cfg.json") as f:
        buggy_dataset = json.load(f)

    with open("fixeval_regular_for_sample.json") as f:
        non_buggy_dataset = json.load(f)

    return buggy_dataset, non_buggy_dataset

def analyze_the_dataset(dataset):
    '''Analyze a dataset to count submissions with imports and map problems to their filtered submissions.

    This function processes a dataset to determine the number of submissions that include 
    the keyword "import" for each problem and creates a mapping of problem IDs to their 
    corresponding submission IDs with imports. It also tracks global statistics.

    Args:
        dataset (dict): A dataset containing problems and their submissions.

    Returns:
        tuple: A tuple containing:
            - prob_count_list (list): A list of tuples, each containing a problem ID and 
              the count of submissions with imports for that problem.
            - prob_sub_mapping (dict): A dictionary mapping each problem ID to a list of 
              its submission IDs containing imports.
    '''
    prob_count_list = []
    prob_sub_mapping = {}
    
    # Track global statistics
    global_count = 0  # Total number of submissions processed
    import_count = 0  # Total number of submissions containing "import"

    for prob in dataset:
        count = 0; temp = []
        for sub in dataset[prob]:
            global_count += 1 # Increment the total submission count
            code = dataset[prob][sub]["code"] # Extract the code from the submission
            
            # Check if the submission contains the keyword "import"
            if "import" in code:
                temp.append(sub) # Add the submission ID to the list
                count += 1 # Increment the count for the current problem
                import_count += 1 # Increment the global import count
        
        # If the problem has any submissions with "import", update the mappings
        if count > 0:
            prob_sub_mapping[prob] = temp # Map the problem ID to its submissions with "import"
            prob_count_list.append((prob, count)) # Add the problem and its count to the list

    return prob_count_list, prob_sub_mapping

def merge_dataset(dataset1, dataset2):
    '''Merge two datasets into a single dataset, ensuring all entries have exception information.

    This function combines two datasets by iterating through each problem ID and submission ID, 
    ensuring that each submission includes an `exception_info` field (set to `None` if missing). 
    The function updates or overwrites entries in the merged dataset if they exist in both inputs.

    Args:
        dataset1 (dict): The first dataset to merge.
        dataset2 (dict): The second dataset to merge.

    Returns:
        dict: A merged dataset containing all problem and submission entries from both input datasets.
    '''
    merged_dataset = {}
    # Process the first dataset
    for prob_id in dataset1:
        for sub_id in dataset1[prob_id]:
            obj = dataset1[prob_id][sub_id]
            if 'exception_info' not in obj:
                obj['exception_info'] = None
            if prob_id not in merged_dataset:    merged_dataset[prob_id] = {}
            if sub_id not in merged_dataset[prob_id]:    merged_dataset[prob_id][sub_id] = {}
            # Add or update the submission in the merged dataset
            merged_dataset[prob_id][sub_id] = obj

    # Process the second dataset
    for prob_id in dataset2:
        for sub_id in dataset2[prob_id]:
            obj = dataset2[prob_id][sub_id]
            if 'exception_info' not in obj:
                obj['exception_info'] = None
            if prob_id not in merged_dataset:    merged_dataset[prob_id] = {}
            if sub_id not in merged_dataset[prob_id]:    merged_dataset[prob_id][sub_id] = {}
            # Add or update the submission in the merged dataset
            merged_dataset[prob_id][sub_id] = obj

    return merged_dataset

def adjust_cfg_ranges(cfg_block_range, cfg_block_statements):
    '''Adjust the ranges and statements of a control flow graph (CFG) by removing import statements.

    This function updates the ranges of code blocks in a CFG after filtering out 
    `import` and `from ...` statements. The new ranges and statements are recalculated 
    based on the remaining lines of code.

    Args:
        cfg_block_range (dict): A dictionary mapping block IDs to their line ranges.
        cfg_block_statements (dict): A dictionary mapping block IDs to their corresponding statements.

    Returns:
        tuple: A tuple containing:
            - new_cfg_block_range (dict): Updated line ranges for each block.
            - new_cfg_block_statements (dict): Updated statements for each block after filtering.
    '''
    current_line = 1
    new_cfg_block_range = {}
    new_cfg_block_statements = {}
    
     # Iterate through blocks sorted by their IDs
    for block_id in sorted(cfg_block_range.keys(), key=lambda x: int(x)):
        statements = cfg_block_statements[block_id]
        
        # Filter out import statements (lines starting with 'import' or 'from')
        new_statements = []
        for line in statements:
            if not (line.strip().startswith('import ') or line.strip().startswith('from ')):
                new_statements.append(line)
        
        # If there are remaining statements, update their ranges and contents
        if new_statements:
            new_start = current_line # New start line for the block
            new_end = current_line + len(new_statements) - 1 # New end line for the block
            new_cfg_block_range[block_id] = {"range": [new_start, new_end]} # Update the range
            new_cfg_block_statements[block_id] = new_statements # Update the statements
            current_line = new_end + 1 # Move to the next line after the current block

    return new_cfg_block_range, new_cfg_block_statements

def process_final_data(merged_dataset):
    '''Process the merged dataset to remove import statements, adjust CFG data, and update execution order.

    This function processes a merged dataset by removing `import` statements from the code and 
    corresponding CFG blocks. It adjusts the block ranges and statements in the CFG and updates 
    the ground truth execution order to reflect the removal of import lines. The processed data 
    is stored in a new dataset along with counts of buggy and non-buggy submissions.

    Args:
        merged_dataset (dict): The input dataset containing problems and their submissions.

    Returns:
        tuple: A tuple containing:
            - final_data (dict): Processed dataset with updated code, CFG, and execution order.
            - buggy_count (int): Total number of buggy submissions in the dataset.
            - non_buggy_count (int): Total number of non-buggy submissions in the dataset.
    '''

    final_data = {}
    buggy_count = 0
    non_buggy_count = 0
    
    # Iterate through problems and submissions in the merged dataset
    for prob, subs in merged_dataset.items():
        for sub_id, sub_data in subs.items():
            
            # Extract relevant data fields
            code = sub_data['code']
            input_cfg = sub_data['input_cfg']
            cfg_block_range = sub_data.get('cfg_block_range')
            cfg_block_statements = sub_data.get('cfg_block_statements')
            exception_info = sub_data.get('exception_info')

            # Increment counters based on whether the submission is buggy
            if exception_info:
                buggy_count += 1
            else:
                non_buggy_count += 1
            
            # Extract ground truth execution order
            ground_truth_execution_order = sub_data['ground_truth_execution_order']
            
            # Skip submissions without import statements
            if 'import' not in code:
                print("No import statement found in the code")
                continue
            
            # Remove import statements and get adjusted code and removed lines
            new_code, removed_lines = remove_imports(code)

            # Adjust CFG block ranges and statements
            new_cfg_block_range, new_cfg_block_statements = adjust_cfg_ranges(cfg_block_range, cfg_block_statements)

            # Ensure all import statements are removed
            if 'import' in new_code:
                print("Import statement still found in the code")
                continue
            
            # Adjust the ground truth execution order based on removed lines
            new_gt = []
            for line in ground_truth_execution_order:
                if line not in removed_lines:
                    # Calculate how many removed lines appeared before the current line
                    adjustment = sum(1 for removed in removed_lines if removed < line)
                    adjusted_line = line - adjustment
                    new_gt.append(adjusted_line)

            # Initialize the problem ID in final_data if not already present
            if prob not in final_data:
                final_data[prob] = {}
            
            # Store the processed data for the submission
            final_data[prob][sub_id] = {
                **sub_data,
                'code': new_code, # Incomplete code without import statements
                'ground_truth_execution_order': new_gt, # Updated execution order
                'cfg_block_range': new_cfg_block_range, # Updated CFG ranges
                'cfg_block_statements': new_cfg_block_statements,  # Updated CFG statements
                'input_cfg': remove_imports_and_blank_lines(input_cfg), # Cleaned input CFG 
            }
    
    return final_data, buggy_count, non_buggy_count

def make_incomplete_dataset(buggy_dataset, non_buggy_dataset):
    # Analyze the datasets to count submissions with imports and map problems to their filtered submissions
    buggy_prob_count_list, valid_buggy_prob_sub_mapping = analyze_the_dataset(buggy_dataset)
    non_buggy_prob_count_list, valid_non_buggy_prob_sub_mapping = analyze_the_dataset(non_buggy_dataset)

    # Define the total count of instances to select from each dataset
    input_size = int(input("\nDo you want to enter the total count of instances to select? (0 for default numbers or 1 for custom input): "))
    if input_size == 0:
        total_count = 374
    elif input_size == 1:
        print("Enter the total count of instances to select (up to 374): ")
        total_count = int(input())
    else:
        print("Invalid Input!, going with default value of 374")
        total_count = 374
    
    selected_buggy_instances_mapping = select_instances(buggy_prob_count_list, total_count)
    selected_nonbuggy_instances_mapping = select_instances(non_buggy_prob_count_list, total_count)
    
    # Select a subset of submissions for each problem based on instance mapping
    selected_buggy_data = select_sub_data(buggy_dataset, selected_buggy_instances_mapping, valid_buggy_prob_sub_mapping)
    selected_non_buggy_data = select_sub_data(non_buggy_dataset, selected_nonbuggy_instances_mapping, valid_non_buggy_prob_sub_mapping)

    # Merge the selected datasets into a single dataset
    merged_data = merge_dataset(selected_non_buggy_data, selected_buggy_data)

    final_data, buggy_count, non_buggy_count = process_final_data(merged_data)

    return final_data
