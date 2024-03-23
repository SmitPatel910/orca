import json
from accuracy import calculate_exact_match, calculate_statement_coverage, calculate_prefix_match, calculate_symbol_table_accuracy

with open('./output/parsed_fixeval_pred_codeExe.json', 'r') as file:
    parsed_prediction = json.load(file)

with open('./dataset/fixeval_cfg_codexe.json', 'r') as file:
    finaldata = json.load(file)

with open('./dataset/fixeval_trace.json', 'r') as file:
    tracedata = json.load(file)

EM = 0
COV_R = 0
COV_P = 0
PRE_R = 0
PRE_P = 0
ST = 0

for id in parsed_prediction.keys():
    pred_symbol_table = parsed_prediction[id]["symbol_table"]
    gt_exe_symbol_table = finaldata[id]['ground_truth_blocks']
    prob = id.split('_')[0]
    sub = id.split('_')[1]
    gt_exe_symbol_table = tracedata[prob][sub]['final_trace']
    pred_exe = parsed_prediction[id]['execution_order']
    gt_exe = finaldata[id]['ground_truth_execution_order']

    try:
        exact_match = calculate_exact_match(pred_exe, gt_exe)
        statement_recall, statement_precision = calculate_statement_coverage(pred_exe, gt_exe)
        prefix_recall, prefix_precision = calculate_prefix_match(pred_exe, gt_exe)
        symbol_table_accuracy = calculate_symbol_table_accuracy(pred_symbol_table, gt_exe_symbol_table)
        EM += exact_match
        COV_R += statement_recall
        COV_P += statement_precision
        PRE_R += prefix_recall
        PRE_P += prefix_precision
        ST += symbol_table_accuracy
    except:
        continue

print(f"Total: {len(parsed_prediction)}")
print()

print("RQ2")
print(f"Exact Match: {100 * (EM/len(parsed_prediction)):.2f}")
print()
print(f"Prefix Match Recall: {100 * (PRE_R/len(parsed_prediction)):.2f}")
print(f"Prefix Match Precision: {100 * (PRE_P/len(parsed_prediction)):.2f}")
print()
print(f"Statement Coverage Recall: {100 * (COV_R/len(parsed_prediction)):.2f}")
print(f"Statement Coverage Precision: {100 * (COV_P/len(parsed_prediction)):.2f}")
print()
print("RQ3")
print(f"Symbol Table Accuracy: {100 * (ST/len(parsed_prediction)):.2f}")
print()
