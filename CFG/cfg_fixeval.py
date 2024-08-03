from absl import app
from tqdm import tqdm
from python_graphs import control_flow
from python_graphs import control_flow_graphviz
from python_graphs import control_flow_test_components as tc
from python_graphs import program_utils

from CFG.utils import replace_code_in_file, reset_file_content
from CFG.utils import extract_statements_range_from_block, get_the_next_block, renumbering_blocks, cfg_to_text, ground_truth_code_blocks_fixeval

def get_cfg_from_function(testFun):
    return control_flow.get_control_flow_graph(testFun)

def process_single_code_submission(code, mode):
    try:
        if mode == 'single':
            from example import testFun
        else:
            reset_file_content('example.py')
            replace_code_in_file('example.py', code)
            from example import testFun

        cfg = get_cfg_from_function(testFun)
        
        if mode == 'single':
            source = program_utils.getsource(testFun)
            control_flow_graphviz.render(cfg, include_src=source, path='cfg.png')

        cfg_block_range, cfg_block_statements = extract_statements_range_from_block(cfg, code)
        if cfg_block_range == None or cfg_block_statements == None: return None
        cfg_next_block = get_the_next_block(cfg_block_range, cfg)
        if cfg_next_block == None: return None
        cfg_block_statements, cfg_block_range, cfg_next_block = renumbering_blocks(cfg_block_statements, cfg_block_range, cfg_next_block)
        if cfg_block_statements == None or cfg_block_range == None or cfg_next_block == None: return None
        return cfg_block_statements, cfg_block_range, cfg_next_block
    
    except Exception as e:
        return None

def handle_user_input():
    input_prefers = input("Running for a single code submission? (y/n): ")
    if input_prefers == 'y':
        with open('example.py', 'r') as file:
            code = file.read()
        process_single_code_submission(code)

    else:
        datasets = process_dataset()
        return datasets

def process_dataset(buggy_dataset, non_buggy_dataset):
    final_dataset = {}
    datasets = {
        'buggy': buggy_dataset,
        'non_buggy': non_buggy_dataset
    }
    for label, fixeval_dataset in datasets.items():
        final_dataset[label] = process_dataset_entries(fixeval_dataset)
    
    return final_dataset

def process_dataset_entries(fixeval_dataset):
    results = {}
    true_count = 0
    false_count = 0
    total = 0
    for prob_id, problem_data in tqdm(fixeval_dataset.items()):
        
        if not problem_data: continue
        
        results[prob_id] = {}
        for sub_id, submission in problem_data.items():
            
            if not submission:  continue
            total += 1
            code = submission['code']
            execution_order = submission['execution_order']
            exe_trace = submission['final_trace']
            exception_info = submission.get('exception_info', None)

            cfg_items = process_single_code_submission(code, 'dataset')
            if cfg_items == None:   false_count += 1; continue

            cfg_block_statements, cfg_block_range, cfg_next_block = cfg_items

            ground_truth_blocks = ground_truth_code_blocks_fixeval(cfg_block_range, execution_order, exe_trace)

            cfg_text = cfg_to_text(cfg_block_statements, cfg_next_block, cfg_block_range)
            if cfg_text == "":    false_count += 1; continue

            results[prob_id][sub_id] = create_submission_entry(code, exception_info, execution_order, ground_truth_blocks, cfg_block_statements, cfg_next_block, cfg_block_range, cfg_text)
            
            true_count += 1
    
    return results

def create_submission_entry(code, exception_info, execution_order, ground_truth_blocks, cfg_block_statements, cfg_next_block, cfg_block_range, cfg_text):
    return {
        'code': code,
        'exception_info': exception_info,
        'ground_truth_execution_order': execution_order,
        'ground_truth_blocks': ground_truth_blocks,
        'cfg_block_statements': cfg_block_statements,
        'cfg_next_block': cfg_next_block,
        'cfg_block_range': cfg_block_range,
        'input_cfg': cfg_text
    }

def generate_cfg(buggy_dataset, non_buggy_dataset):
    # handle_user_input()
    cfg_datasets = process_dataset(buggy_dataset, non_buggy_dataset)
    return cfg_datasets['buggy'], cfg_datasets['non_buggy']