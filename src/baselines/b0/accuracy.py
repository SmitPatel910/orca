def get_gt_execution_order(actuals):
    execution_order = []
    for line in actuals:
        block_number = line['block']
        execution_order.append(int(block_number))
    return execution_order

def get_gt_execution_trace(actuals):
    execution_trace = []
    for line in actuals:
        block_number = line['line']
        symbol_table = {}
        if len(line['var_val']) == 0:
            execution_trace.append({"line": int(block_number), "symbol_table": symbol_table})
            continue
        for each_state in line['var_val']:
            symbol_table[list(each_state.keys())[0]] = list(each_state.values())[0]
        execution_trace.append({"line": int(block_number), "symbol_table": symbol_table})
    return execution_trace

def calculate_exact_match(predictions, actuals):
    try:
        if len(predictions) != len(actuals):
            return 0
        for i in range(len(predictions)):
            if predictions[i] != actuals[i]:
                return 0
        return 1
    except:
        return None
    
# Statement coverage
def calculate_statement_coverage(predictions, actuals):
    try:
        if len(actuals) == 0: 
            return None, None
        if len(predictions) == 0: 
            return None, None
        correct = 0; total = 0

        gt_set = set(actuals)
        for gt_line in actuals:
            gt_set.add(gt_line)

        pred_set = set(predictions)
        for pd_line in predictions:
            pred_set.add(pd_line)

        correct = len(gt_set.intersection(pred_set))
        stat_cov_recall = correct / len(gt_set)
        stat_cov_precision = correct / len(pred_set)
        return stat_cov_recall, stat_cov_precision
    except:
        return None, None

# Prefix Match
def calculate_prefix_match(predictions, actuals):
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

# Symbol table accuracy
def calculate_symbol_table_accuracy(pred_symbol_table, actuals):
    try:
        actuals = get_gt_execution_trace(actuals)
        pred_symbol_table = pred_symbol_table
        gt_symbol_table = actuals
        correct_match = 0
        incorrect_match = 0
   
        for index, pd_block in enumerate(pred_symbol_table):
            if index >= len(actuals): break
            if not pd_block['line'] == actuals[index]['line']: continue
            if pd_block['symbol_table'] == "": continue
            pred_symbol_table = pd_block['symbol_table']
            gt_symbol_table = actuals[index]['symbol_table']
            for key in pred_symbol_table.keys():
                if not key in gt_symbol_table: continue
                gt = gt_symbol_table[key]
                if gt.startswith('"') or gt.startswith("'"):    gt = gt[1:]
                if gt.endswith('"') or gt.endswith("'"):   gt = gt[:-1]
                pred_value = pred_symbol_table[key]
                pred_value = eval(pred_value)
                if isinstance(pred_value, list):
                    pred_value = [f'{item}' for item in pred_value]
                    pred_value = str(pred_value)
                else:
                    pred_value = str(pred_value)
                if pred_value == gt:
                    correct_match += 1
                else:
                    incorrect_match += 1

        if correct_match + incorrect_match == 0: return None
        accuracy  = correct_match / (correct_match + incorrect_match)
        
        return accuracy
        
    except:
        return None

    