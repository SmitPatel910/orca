# Exact Match Accuracy
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

# Prefix Matching: Recall, Precision
def calculate_prefix(predictions, actuals):
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

# Statement Coverage: Recall, Precision
def calculate_statement_coverage(predictions, actuals):
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
        block_recall = correct / len(gt_set)
        block_precision = correct / len(pred_set)
        return block_recall, block_precision
    except:
        return None, None
    
# Error Location Matching
def calculate_error_location(statement_exe, actuals):
    try:
        gt_error_block = int(actuals[-1])
        pd_error_block = int(statement_exe[-1])
        if pd_error_block == gt_error_block: return 1
        else: return 0
    except:
        return None

# Error type Matching
def calculate_error_type(predictions, exception_info):
    try:
        import re
        pattern = r"TypeError"
        match = re.search(pattern, exception_info['class'])
        if match: 
            exception_info = "TypeError"
            if predictions.lower().strip() == exception_info.lower().strip(): return 1
            else: return 0
        else: 
            return 1
    except:
        return None
