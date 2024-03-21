import json
import time
from model import AgentInteraction
from utils import output_parser
from accuracy import calculate_exact_match, calculate_statement_coverage,  calculate_prefix, calculate_error_location, calculate_error_type

with open('dataset/fixeval_cfg.json') as f:
    data = json.load(f)

def calculate_accuracy(statement_exe, ground_truth_execution_order, error_type, exception_info, is_error):
    exact_match = None; statement_cov_recall = None; statement_cov_precision = None; prefix_match_recall = None; prefix_match_precision = None; error_line_match = None; error_type_match = None

    if statement_exe:
        exact_match = calculate_exact_match(statement_exe, ground_truth_execution_order)
        statement_cov_recall, statement_cov_precision = calculate_statement_coverage(statement_exe, ground_truth_execution_order)
        prefix_match_recall, prefix_match_precision = calculate_prefix(statement_exe, ground_truth_execution_order)
        error_line_match = calculate_error_location(statement_exe, ground_truth_execution_order)

    if error_type != "":
        error_type_match = calculate_error_type(error_type, exception_info)

    accuracy = {"EM": exact_match, "PRE": [prefix_match_recall, prefix_match_precision],"COV": [statement_cov_recall, statement_cov_precision], "ErrorLocation": error_line_match, "ErrorType": error_type_match, "Is_Error": is_error}
    return accuracy

def gpt_pipeline(id, code, ground_truth_execution_order, exception_info):
    agent = AgentInteraction()
    system = agent.init_system_prompt()
    user_Template = agent.init_user_prompt()

    system = agent.apply_zero_shot(system)
    user = agent.add_testing_snippet(user_Template, code)
    message = [{"role": "system", "content": system}, {"role": "user", "content": user}]

    try:
        # API Call
        s_time = time.time()
        output, response = agent.api_call(message)
        e_time = time.time()
        # Output Parser
        statement_exe, [error_type, is_error] = output_parser(output)
        accuracy = calculate_accuracy(statement_exe, ground_truth_execution_order, error_type, exception_info, is_error)            
        pred = {"statement_execution": str(statement_exe), "error_type": error_type, "is_error": is_error}
        return accuracy, pred, e_time - s_time, output
    except Exception as e:
        print(f"API Call Failed! Error: {e}")
        return {}, {}, {}, "API Call Failed!"
    
baseline_b0 = {}
count = 0
for prob in data.keys():
    if data[prob] == {}: continue
    baseline_b0[prob] = {}
    submissions = {}
    for index, sub in enumerate(data[prob].keys()):
        if data[prob][sub] == {}: continue
        submissions[sub] = {}
        code = data[prob][sub]['code']
        ground_truth_execution_order = data[prob][sub]['ground_truth_execution_order']
        exception_info = data[prob][sub]['exception_info']
        count += 1
        print(f"Problem: {prob}, Sub: {sub}, Index: {index}, Count: {count}")
        accuracy, pred, pred_time, output = gpt_pipeline(sub, code, ground_truth_execution_order, exception_info)
        submissions[sub] = {"accuracy": accuracy, "pred": pred, "pred_time": pred_time, "gt": ground_truth_execution_order, "output": output}
        print("=======================================================================================================================")
    baseline_b0[prob] = submissions

with open('output/output_b1.json', 'w') as file:
    json.dump(baseline_b0, file)