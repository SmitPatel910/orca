import json
from utils import get_statements_from_blocks
from accuracy import get_statement_coverage, get_statement_prefix

with open('./output/output_fixeval_cfg.json', 'r') as file:
    response_cache = json.load(file)
with open('../../dataset/fixeval_cfg.json', 'r') as file:
    dataset = json.load(file)

# RQ1
EB = 0
ET = 0

# RQ2
EM = 0

Block_Pre_R = 0
Block_Pre_P = 0
Statement_Pre_R = 0
Statement_Pre_P = 0

Block_Cov_R = 0
Block_Cov_P = 0
Statement_Cov_R = 0
Statement_Cov_P = 0

Block_Transition_R = 0
Block_Transition_P = 0

# RQ3
ST = 0

count = 0
execution_count = 0
error_count = 0
symbol_table_count = 0
special_list = []

for prob in response_cache:
    for sub in response_cache[prob]:
        if response_cache[prob][sub] == {}: continue
        if response_cache[prob][sub]['accuracy'] == {}: continue
        # Pred and GT
        pred_blocks = response_cache[prob][sub]['pred']
        gt_blocks = response_cache[prob][sub]['gt']
        block_range = dataset[prob][sub]['cfg_block_range']
        pd_statement, gt_statement = get_statements_from_blocks(block_range, pred_blocks, gt_blocks)
        accuracy = response_cache[prob][sub]['accuracy']

        # RQ1
        if accuracy['EB'] != None: error_count += 1; EB += accuracy['EB']
        if accuracy['EB'] != None and accuracy['EB'] == 1 and accuracy['ST'] == 1: special_list.append((prob, sub))
        if accuracy['ET'] != None:  ET += accuracy['ET']
        # if accuracy['is_error'] == True:  error_count += 1

        # RQ2
        if accuracy['EM'] != None:  execution_count += 1; EM += accuracy['EM']
        
        if accuracy['PF'][0] != None and accuracy['PF'][1] != None:  Block_Pre_R += accuracy['PF'][0]; Block_Pre_P += accuracy['PF'][1]
        stat_pre_r, stat_pre_p = get_statement_prefix(pd_statement, gt_statement)
        if stat_pre_r != None and stat_pre_p != None:  Statement_Pre_R += stat_pre_r; Statement_Pre_P += stat_pre_p

        if accuracy['BM'][0] != None and accuracy['BM'][1] != None:  Block_Cov_R += accuracy['BM'][0]; Block_Cov_P += accuracy['BM'][1]
        stat_cov_r, stat_cov_p = get_statement_coverage(pd_statement, gt_statement)
        if stat_cov_r != None and stat_cov_p != None:  Statement_Cov_R += stat_cov_r; Statement_Cov_P += stat_cov_p

        if accuracy['CF'][0] != None and accuracy['CF'][1] != None:  Block_Transition_R += accuracy['CF'][0]; Block_Transition_P += accuracy['CF'][1]

        # RQ3
        if accuracy['ST'] != None:  symbol_table_count += 1; ST += accuracy['ST']
        count += 1
        
print(f"Total: {count}")
print()
print("RQ1")
print(f"Is Error: {100 * (error_count/count):.2f}")
print(f"Error Block: {100 * (EB/count):.2f}")
print()

print("RQ2")
print(f"Exact Match: {100 * (EM/count):.2f}")
print()
print(f"Prefix Block Recall: {100 * (Block_Pre_R/count):.2f}")
print(f"Prefix Statement Recall: {100 * (Statement_Pre_R/count):.2f}")
print(f"Prefix Block Precision: {100 * (Block_Pre_P/count):.2f}")
print(f"Prefix Statement Precision: {100 * (Statement_Pre_P/count):.2f}")
print()
print(f"Block Coverage Recall: {100 * (Block_Cov_R/count):.2f}")
print(f"Statement Coverage Recall: {100 * (Statement_Cov_R/count):.2f}")
print(f"Block Coverage Precision: {100 * (Block_Cov_P/count):.2f}")
print(f"Statement Coverage Precision: {100 * (Statement_Cov_P/count):.2f}")
print()
print(f"Block Transition Recall: {100 * (Block_Transition_R/count):.2f}")
print(f"Block Transition Precision: {100 * (Block_Transition_P/count):.2f}")
print()

# RQ3
print("RQ3")
print(f"Symbol Table: {100 * (ST/count):.2f}")
print(f"Total Symbol table: {symbol_table_count:.2f}")
print(f"Correct Error Block and ST is 100 : {len(special_list)}")