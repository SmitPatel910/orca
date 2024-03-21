import os
import json
import time
from model import AgentInteraction
from utils import output_parser
from accuracy import calculate_exact_match_accuracy, calculate_control_flow_accuracy, calculate_block_accuracy, calculate_prefix_accuracy, calculate_error_block_accuracy, calculate_error_type_accuracy, calculate_symbol_table_accuracy

def calculate_accuracy(block_execution, ground_truth_blocks, error_type, error_block, exception_info, block_symbol_table, is_error):
    exact_match = None; control_flow_recall = None; control_flow_precision = None; block_match_recall = None; block_match_precision = None; prefix_match_recall = None; prefix_match_precision = None; symbol_match = None; error_block_match = None; error_type_match = None
    if block_execution:
        exact_match = calculate_exact_match_accuracy(block_execution, ground_truth_blocks)
        control_flow_recall, control_flow_precision  = calculate_control_flow_accuracy(block_execution, ground_truth_blocks)
        block_match_recall, block_match_precision = calculate_block_accuracy(block_execution, ground_truth_blocks)
        prefix_match_recall, prefix_match_precision = calculate_prefix_accuracy(block_execution, ground_truth_blocks)
        symbol_match = calculate_symbol_table_accuracy(block_symbol_table, ground_truth_blocks)

    if error_type != "" and error_block != "":
        error_block_match = calculate_error_block_accuracy(error_block, ground_truth_blocks)
        error_type_match = calculate_error_type_accuracy(error_type, exception_info)

    accuracy = {"EM": exact_match, "CF": [control_flow_recall, control_flow_precision], "BM": [block_match_recall, block_match_precision], "PF": [prefix_match_recall, prefix_match_precision], "ST": symbol_match, "EB": error_block_match, "ET": error_type_match, "is_error": is_error}
    return accuracy

def gpt_pipeline(id, input_cfg, ground_truth_blocks, exception_info, recursive=False, recursive_count=0):
    agent = AgentInteraction()
    system = agent.init_system_prompt()
    user_Template = agent.init_user_prompt()

    system = agent.apply_zero_shot(system)
    user = agent.add_testing_snippet(user_Template, input_cfg)
    message = [{"role": "system", "content": system}, {"role": "user", "content": user}]

    try:
        # API Call
        s_time = time.time()
        if recursive == True:
            output, response = agent.api_call(message, temmprature=0.7, seed=50)
        else:
            output, response = agent.api_call(message)
        e_time = time.time()
    
        # Output Parser
        block_execution, [error_type, error_block, is_error], block_symbol_table = output_parser(output, response)

        if block_execution == []:
            if recursive_count < 3:
                recursive_count += 1
                gpt_pipeline(id, input_cfg, ground_truth_blocks, exception_info, recursive=True, recursive_count=recursive_count)
        
        accuracy = calculate_accuracy(block_execution, ground_truth_blocks, error_type, error_block, exception_info, block_symbol_table, is_error)            
        pred = {"block_execution": block_execution, "error_type": error_type, "error_block": error_block}
        return accuracy, pred, e_time - s_time, output
    except:
        return {}, {}, {}, "API Call Failed!"

if __name__ == "__main__":
    with open('../../dataset/fixeval_cfg.json', 'r') as file:
        fixeval_cfg = json.load(file)
        
    response_cache = {}
    count = 0
    flag = False
    for prob in fixeval_cfg:
        if fixeval_cfg[prob] == {}: continue
        response_cache[prob] = {}
        submissions = {}
        for index, sub in enumerate(fixeval_cfg[prob]):
            if fixeval_cfg[prob][sub] == {}: continue
            submissions[sub] = {}
            code = fixeval_cfg[prob][sub]['code']
            cfg_block_range = fixeval_cfg[prob][sub]['cfg_block_range']
            ground_truth_blocks = fixeval_cfg[prob][sub]['ground_truth_blocks']
            exception_info = fixeval_cfg[prob][sub]['exception_info']['class']
            cfg_block_statements = fixeval_cfg[prob][sub]['cfg_block_statements']
            cfg_next_block = fixeval_cfg[prob][sub]['cfg_next_block']
            input_cfg = fixeval_cfg[prob][sub]['input_cfg']
            count += 1
            print(f"Problem: {prob}, Sub: {sub}, Index: {index}, Count: {count}")
            accuracy, pred, pred_time, output = gpt_pipeline(sub, input_cfg, ground_truth_blocks, exception_info)
            submissions[sub] = {"accuracy": accuracy, "pred": pred, "pred_time": pred_time, "gt": ground_truth_blocks, "output": output}
        response_cache[prob] = submissions
        
    with open('output/output_fixeval_cfg.json', 'w') as file:
        json.dump(response_cache, file)


