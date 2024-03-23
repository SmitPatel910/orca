import inspect
import os
from absl import app
from python_graphs import control_flow
from python_graphs import control_flow_graphviz
from python_graphs import control_flow_test_components as tc
from python_graphs import program_utils

 
import json
from tqdm import tqdm
from utils import replace_code_in_file, reset_file_content, extract_statements_range_from_block, get_the_next_block, renumbering_blocks, make_cfg_into_code
from utils import ground_truth_code_blocks_fixeval


def read_cfg(cfg, code):
    block_range, block_statements = extract_statements_range_from_block(cfg, code, code)
    next_block = get_the_next_block(block_range, cfg)
    return block_statements, block_range, next_block
 
def make_cfg(code, Code):
    try:
        reset_file_content('example.py')
        replace_code_in_file('example.py', code)
        from example import testFun
        cfg = control_flow.get_control_flow_graph(testFun)
        cfg_block_statements, cfg_block_range, cfg_next_block = read_cfg(cfg, code)
        f_cfg_block_statements, f_cfg_block_range, f_cfg_next_block = renumbering_blocks(cfg_block_statements, cfg_block_range, cfg_next_block)
        input_cfg = make_cfg_into_code(f_cfg_block_statements, f_cfg_next_block, f_cfg_block_range)
        if input_cfg == "": return None, None, None, None
        return f_cfg_block_statements, f_cfg_block_range, f_cfg_next_block, input_cfg
    except Exception as e:
        return None, None, None, None
 
if __name__ == '__main__':
    with open('../../dataset/fixeval_crash_for_cfg.json','r') as file:
        fixeval_dataset = json.load(file)
    # cfg_dataset
    count = 0
    total = 0
    true = 0
    final_dataset = {}
    for prob_id in tqdm(fixeval_dataset):
        if fixeval_dataset[prob_id] == {}: continue
        final_dataset[prob_id] = {}
        submissions = {}
        for sub_id in fixeval_dataset[prob_id]:
            if fixeval_dataset[prob_id][sub_id] == {}: continue
            total += 1
            code = fixeval_dataset[prob_id][sub_id]['code']
            execution_order = fixeval_dataset[prob_id][sub_id]['execution_order']
            exe_trace = fixeval_dataset[prob_id][sub_id]['final_trace']
            cfg_block_statements, cfg_block_range, cfg_next_block, input_cfg = make_cfg(code, code)
            if cfg_block_statements == None or cfg_block_range == None or cfg_next_block == None or input_cfg == None: count += 1; continue
            # Modify the ground truth into the blocks
            ground_truth_blocks = ground_truth_code_blocks_fixeval(cfg_block_range, execution_order, exe_trace)
            true += 1
            temp = {
                'code': code,
                'cfg_block_range': cfg_block_range,
                'ground_truth_execution_order': execution_order,
                'ground_truth_blocks': ground_truth_blocks,
                'exception_info': fixeval_dataset[prob_id][sub_id]['exception_info'],
                'cfg_block_statements': cfg_block_statements,
                'cfg_next_block': cfg_next_block,
                'input_cfg': input_cfg
            }
            submissions[sub_id] = temp
        final_dataset[prob_id] = submissions

    print(f"Total Instances: {total}")
    print(f"True Instances: {true}")
    print(f"False Instances: {count}")
    
    with open('../../dataset/fixeval_crash_for_sample.json','w') as file:
        json.dump(final_dataset, file)
