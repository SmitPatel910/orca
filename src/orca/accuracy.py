def get_gt_execution_order(actuals):
    execution_order = []
    for line in actuals:
        block_number = line['block']
        execution_order.append(int(block_number))
    return execution_order

def get_gt_execution_trace(actuals):
    execution_trace = []
    for line in actuals:
        block_number = line['block']
        symbol_table = {}
        if line['state'] == []:
            execution_trace.append({"block_id": int(block_number), "symbol_table": symbol_table})
            continue
        for each_state in line['state']:
            symbol_table[list(each_state.keys())[0]] = list(each_state.values())[0]
        execution_trace.append({"block_id": int(block_number), "symbol_table": symbol_table})
    return execution_trace

# Exact Match Accuracy
def calculate_exact_match_accuracy(predictions, actuals):
    try:
        actuals = get_gt_execution_order(actuals)
        if len(predictions) != len(actuals):
            return 0
        for i in range(len(predictions)):
            if predictions[i] != actuals[i]:
                return 0
        return 1
    except:
        return None

# Control flow accuracy Recall, Precision
def calculate_control_flow_accuracy(predictions, actuals):
    try:
        actuals = get_gt_execution_order(actuals)
        if len(actuals) == 0: 
            return None, None
        if len(predictions) == 0: 
            return None, None
        correct = 0; total = 0

        if len(actuals) == 1 and len(predictions) == 1:
            if predictions[0] == actuals[0]: 
                return 1, 1
            else: 
                return 0, 0

        gt_block_transition = set()
        pd_block_transition = set()
        for i in range(len(actuals) - 1):
            gt_block_transition.add((actuals[i], actuals[i+1]))
        for i in range(len(predictions) - 1):
            pd_block_transition.add((predictions[i], predictions[i+1]))

        correct = len(pd_block_transition.intersection(gt_block_transition))
        control_flow_recall = correct / len(gt_block_transition)
        control_flow_precision = correct / len(pd_block_transition)
        return control_flow_recall, control_flow_precision
    except:
        return None, None

# Block accuracy Recall, Precision // coverage
def calculate_block_accuracy(predictions, actuals):
    try:
        actuals = get_gt_execution_order(actuals)
        if len(actuals) == 0: 
            return None, None
        if len(predictions) == 0: 
            return None, None
        correct = 0; total = 0

        gt_set = set(actuals)
        for gt_block in actuals:
            gt_set.add(gt_block)

        pred_set = set(predictions)
        for pd_block in predictions:
            pred_set.add(pd_block)

        correct = len(gt_set.intersection(pred_set))
        block_recall = correct / len(gt_set)
        block_precision = correct / len(pred_set)
        return block_recall, block_precision
    except:
        return None, None

# Prefix accuracy (First wrong prediction) Recall
def calculate_prefix_accuracy(predictions, actuals):
    try:
        actuals = get_gt_execution_order(actuals)
        if len(actuals) == 0: 
            return None, None
        if len(predictions) == 0: 
            return None, None

        last_index = min(len(actuals),len(predictions))
        for i in range(last_index):
            if predictions[i] != actuals[i]:
                prefix_recall = i / len(actuals)
                prefix_precision = i / len(predictions)
                return prefix_recall, prefix_precision
        prefix_recall = last_index / len(actuals)
        prefix_precision = last_index / len(predictions)
        return prefix_recall, prefix_precision
    except:
        return None, None

# Symbol table accuracy
def calculate_symbol_table_accuracy(block_symbol_table, actuals):
    try:
        actuals = get_gt_execution_trace(actuals)
        correct_match = 0
        incorrect_match = 0
        pred_block_id_symbol_table = block_symbol_table

        for index, pd_block in enumerate(pred_block_id_symbol_table):
            if index >= len(actuals): break
            if not pd_block['block_id'] == actuals[index]['block_id']: continue
            if pd_block['symbol_table'] == "": continue
            pred_symbol_table = pd_block['symbol_table']
            gt_symbol_table = actuals[index]['symbol_table']
            for key in pred_symbol_table.keys():
                if not key in gt_symbol_table: continue
                gt = gt_symbol_table[key]
                if gt.startswith('"') or gt.startswith("'"):    gt = gt[1:]
                if gt.endswith('"') or gt.endswith("'"):   gt = gt[:-1]
                gt = str(gt).strip()
                pred_value = pred_symbol_table[key][0]
                pred_value = str(pred_value).strip()
                if pred_value == gt:
                    correct_match += 1
                else:
                    incorrect_match += 1
        if correct_match + incorrect_match == 0: return None
        accuracy  = correct_match / (correct_match + incorrect_match)
        return accuracy
    except:
        return None

# Error matching block accuracy
def calculate_error_block_accuracy(predictions, actuals):
    try:
        actuals = get_gt_execution_order(actuals)
        gt_error_block = int(actuals[-1])
        pd_error_block = int(predictions)
        if pd_error_block == gt_error_block: return 1
        else: return 0
    except:
        return None

# Error type accuracy
def calculate_error_type_accuracy(predictions, exception_info):
    try:
        import re
        pattern = r"TypeError"
        match = re.search(pattern, exception_info)
        if match: 
            exception_info = "TypeError"
            if predictions.lower().strip() == exception_info.lower().strip(): return 1
            else: return 0
        else: 
            return 1
    except:
        return None

# Statement Level Coverage
def get_statement_coverage(predictions, actuals):
    try:
        if len(actuals) == 0: 
            return None, None
        if len(predictions) == 0: 
            return None, None
        correct = 0

        gt_set = set(actuals)
        for gt_block in actuals:
            gt_set.add(gt_block)

        pred_set = set(predictions)
        for pd_block in predictions:
            pred_set.add(pd_block)

        correct = len(gt_set.intersection(pred_set))
        statement_recall = correct / len(gt_set)
        statement_precision = correct / len(pred_set)
        return statement_recall, statement_precision
    except:
        return None, None
    
# Statement Level PreFix
def get_statement_prefix(predictions, actuals):
    try:
        if len(actuals) == 0: 
            return None, None
        if len(predictions) == 0: 
            return None, None

        last_index = min(len(actuals),len(predictions))
        for i in range(last_index):
            if predictions[i] != actuals[i]:
                prefix_recall = i / len(actuals)
                prefix_precision = i / len(predictions)
                return prefix_recall, prefix_precision
        prefix_recall = last_index / len(actuals)
        prefix_precision = last_index / len(predictions)
        return prefix_recall, prefix_precision
    except:
        return None, None

