import json
with open('output/output_b2.json', 'r') as file:
    response_cache = json.load(file)

# ============== RQ1 ==============
# Error Statement
ErrorLocation = 0
# Error Type
ErrorType = 0
# Error Detected
Is_Error = 0
# ============== RQ2 ==============
# Exact Match
EM = 0
# Statement Coverage
COV_R = 0
COV_P = 0
# Prefix Matching
PRE_R = 0
PRE_P = 0


count = 0
execution_count = 0
error_count = 0

for prob in response_cache:
    for sub in response_cache[prob]:
        if response_cache[prob][sub] == {}: continue
        if response_cache[prob][sub]['accuracy'] == {}: continue
        accuracy = response_cache[prob][sub]['accuracy']
        # RQ1
        if accuracy['Is_Error'] != None:  
            if accuracy['Is_Error']: Is_Error += 1
        if accuracy['ErrorLocation'] != None:  ErrorLocation += accuracy['ErrorLocation']
        # if accuracy['ErrorType'] != None:  ErrorType += accuracy['ErrorType']

        # RQ2
        if accuracy['EM'] != None:  execution_count += 1; EM += accuracy['EM']
        if accuracy['PRE'][0] != None and accuracy['PRE'][1] != None:  PRE_R += accuracy['PRE'][0]; PRE_P += accuracy['PRE'][1]
        if accuracy['COV'][0] != None and accuracy['COV'][1] != None:  COV_R += accuracy['COV'][0]; COV_P += accuracy['COV'][1]
        count += 1
        
print(f"Total: {count}")
print()
print("RQ1")
print(f"Is Error: {100 * (Is_Error/count):.2f}")
print(f"Error Localization: {100 * (ErrorLocation/count):.2f}")
print()
print("RQ2")
print(f"Exact Match: {100 * (EM/count):.2f}")
print()
print(f"Prefix Recall: {100 * (PRE_R/count):.2f}")
print(f"Prefix Precision: {100 * (PRE_P/count):.2f}")
print()
print(f"Statement Cov. Recall: {100 * (COV_R/count):.2f}")
print(f"Statement Cov. Precision: {100 * (COV_P/count):.2f}")
print()