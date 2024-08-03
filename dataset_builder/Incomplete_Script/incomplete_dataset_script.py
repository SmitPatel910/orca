import json
import random
import ast

class ImportRemover(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.removed_lines = []

    def visit_Import(self, node):
        self.removed_lines.append(node.lineno)
        return None

    def visit_ImportFrom(self, node):
        self.removed_lines.append(node.lineno)
        return None

def remove_imports(code):
    tree = ast.parse(code)
    remover = ImportRemover()
    new_tree = remover.visit(tree)
    new_code = ast.unparse(new_tree)
    return new_code, remover.removed_lines

def remove_imports_and_blank_lines(code):
    lines = [line for line in code.split('\n') if not (line.strip().startswith('import ') or line.strip().startswith('from '))]
    return '\n'.join(lines)

def select_instances(prob_count_list, total_count):
    selected_instances = []
    instances_per_category = total_count // len(prob_count_list)
    
    for prob, count in prob_count_list:
        selected_instances.extend([prob] * min(instances_per_category, count))
    
    remaining_count = total_count - len(selected_instances)
    
    if remaining_count > 0:
        remaining_instances = []
        for prob, count in prob_count_list:
            remaining_instances.extend([prob] * max(0, count - instances_per_category))
        
        random.shuffle(remaining_instances)
        selected_instances.extend(remaining_instances[:remaining_count])
    
    instance_map = {}
    for prob in selected_instances:
        if prob not in instance_map:
            instance_map[prob] = 0
        instance_map[prob] += 1

    return instance_map

def select_sub_data(dataset, instance_map, prob_sub_mapping):
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
    prob_count_list = []
    prob_sub_mapping = {}
    global_count = 0
    import_count = 0
    for prob in dataset:
        count = 0; temp = []
        for sub in dataset[prob]:
            global_count += 1
            code = dataset[prob][sub]["code"]
            if "import" in code:
                temp.append(sub)
                count += 1
                import_count += 1
        if count > 0:
            prob_sub_mapping[prob] = temp
            prob_count_list.append((prob, count))
    
    # print("Total Instances:", global_count)
    # print("Instances with Import:", import_count)
    return prob_count_list, prob_sub_mapping

def merge_dataset(dataset1, dataset2):
    merged_dataset = {}
    for prob_id in dataset1:
        for sub_id in dataset1[prob_id]:
            obj = dataset1[prob_id][sub_id]
            if 'exception_info' not in obj:
                obj['exception_info'] = None
            if prob_id not in merged_dataset:    merged_dataset[prob_id] = {}
            if sub_id not in merged_dataset[prob_id]:    merged_dataset[prob_id][sub_id] = {}
            merged_dataset[prob_id][sub_id] = obj

    for prob_id in dataset2:
        for sub_id in dataset2[prob_id]:
            obj = dataset2[prob_id][sub_id]
            if 'exception_info' not in obj:
                obj['exception_info'] = None
            if prob_id not in merged_dataset:    merged_dataset[prob_id] = {}
            if sub_id not in merged_dataset[prob_id]:    merged_dataset[prob_id][sub_id] = {}
            merged_dataset[prob_id][sub_id] = obj

    return merged_dataset

def adjust_cfg_ranges(cfg_block_range, cfg_block_statements):
    current_line = 1
    new_cfg_block_range = {}
    new_cfg_block_statements = {}
    
    for block_id in sorted(cfg_block_range.keys(), key=lambda x: int(x)):
        statements = cfg_block_statements[block_id]
        
        new_statements = []
        for line in statements:
            if not (line.strip().startswith('import ') or line.strip().startswith('from ')):
                new_statements.append(line)
        
        if new_statements:
            new_start = current_line
            new_end = current_line + len(new_statements) - 1
            new_cfg_block_range[block_id] = {"range": [new_start, new_end]}
            new_cfg_block_statements[block_id] = new_statements
            current_line = new_end + 1

    return new_cfg_block_range, new_cfg_block_statements

def process_final_data(merged_dataset):
    final_data = {}
    buggy_count = 0
    non_buggy_count = 0
    
    for prob, subs in merged_dataset.items():
        for sub_id, sub_data in subs.items():
            code = sub_data['code']
            input_cfg = sub_data['input_cfg']
            cfg_block_range = sub_data.get('cfg_block_range')
            cfg_block_statements = sub_data.get('cfg_block_statements')

            exception_info = sub_data.get('exception_info')
            if exception_info:
                buggy_count += 1
            else:
                non_buggy_count += 1
            
            ground_truth_execution_order = sub_data['ground_truth_execution_order']
            
            if 'import' not in code:
                print("No import statement found in the code")
                continue
            
            # Code without imports and Line Number List of Removed Imports
            new_code, removed_lines = remove_imports(code)
            # Adjust CFG Block Range and Statements
            new_cfg_block_range, new_cfg_block_statements = adjust_cfg_ranges(cfg_block_range, cfg_block_statements)

            if 'import' in new_code:
                print("Import statement still found in the code")
                continue

            new_gt = []
            for line in ground_truth_execution_order:
                if line not in removed_lines:
                    # Adjust the line number by counting how many removed lines were before it
                    adjustment = sum(1 for removed in removed_lines if removed < line)
                    adjusted_line = line - adjustment
                    new_gt.append(adjusted_line)

            if prob not in final_data:
                final_data[prob] = {}
            final_data[prob][sub_id] = {
                **sub_data,
                'code': new_code,
                'ground_truth_execution_order': new_gt,
                'cfg_block_range': new_cfg_block_range,
                'cfg_block_statements': new_cfg_block_statements,
                'input_cfg': remove_imports_and_blank_lines(input_cfg),
                
            }
    
    return final_data, buggy_count, non_buggy_count

def make_incomplete_dataset(buggy_dataset, non_buggy_dataset):
    buggy_prob_count_list, valid_buggy_prob_sub_mapping = analyze_the_dataset(buggy_dataset)
    non_buggy_prob_count_list, valid_non_buggy_prob_sub_mapping = analyze_the_dataset(non_buggy_dataset)

    # Sort list descending by count
    total_count = 374
    selected_buggy_instances_mapping = select_instances(buggy_prob_count_list, total_count)
    selected_nonbuggy_instances_mapping = select_instances(non_buggy_prob_count_list, total_count)

    selected_buggy_data = select_sub_data(buggy_dataset, selected_buggy_instances_mapping, valid_buggy_prob_sub_mapping)
    selected_non_buggy_data = select_sub_data(non_buggy_dataset, selected_nonbuggy_instances_mapping, valid_non_buggy_prob_sub_mapping)

    merged_data = merge_dataset(selected_non_buggy_data, selected_buggy_data)

    final_data, buggy_count, non_buggy_count = process_final_data(merged_data)

    return final_data
