# Exact Match Accuracy
def calculate_exact_match(predictions, actuals):
    '''Calculate whether two lists of predictions and actuals match exactly.

    This function checks if the `predictions` list matches the `actuals` list element by element. 
    If they are of different lengths or any element does not match, it returns `0`. If they 
    match exactly, it returns `1`. If an unexpected error occurs, it returns `None`.

    Arguments:
        predictions (list): A list of predicted values.
        actuals (list): A list of actual ground truth values.

    Returns:
        int: Returns `1` if the predictions and actuals match exactly, `0` if they do not match, 
             or if their lengths differ.
        None: Returns `None` if an unexpected error occurs.
    '''
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
    '''Calculate prefix match accuracy between predictions and actuals.

    This function evaluates upto which point the `predictions` list matches the `actuals` list from the beginning (prefix).
    
    It computes prefix recall and precision as follows:
        - Prefix Recall = (Length of Matching Prefix) / (Length of Actuals)
        - Prefix Precision = (Length of Matching Prefix) / (Length of Predictions)

    Arguments:
        predictions (list): A list of predicted values.
        actuals (list): A list of ground truth values.

    Returns:
        tuple: A tuple containing:
            - prefix_recall (float or None): The recall of the prefix match, calculated as 
              the fraction of the ground truth matched by the prefix.
              Returns `None` if `actuals` is empty.
            - prefix_precision (float or None): The precision of the prefix match, calculated as 
              the fraction of the predictions that match the prefix.
              Returns `None` if `predictions` is empty.
    '''
    try:
        if len(actuals) == 0: 
            return None, None
        if len(predictions) == 0: 
            return None, None

        # Iterate upto the length of the shortest list
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
    '''Calculates the recall and precision of statement coverage between predicted and actual executions.

    Arguments:
        predictions (list): A list of predicted executed statements.
        actuals (list): A list of ground truth executed statements.

    Returns:
        tuple: A tuple containing:
            - stat_cov_recall (float or None): The recall of statement coverage, calculated as:
              (correctly predicted statements) / (total ground truth statements).
              Returns `None` if `actuals` is empty or an error occurs.

            - stat_cov_precision (float or None): The precision of statement coverage, calculated as:
              (correctly predicted statements) / (total predicted statements).
              Returns `None` if `predictions` is empty or an error occurs.
    '''
    try:
        if len(actuals) == 0: 
            return None, None
        if len(predictions) == 0: 
            return None, None
        
        correct = 0
        # Ground truth set
        gt_set = set(actuals)
        for gt_block in actuals:
            gt_set.add(gt_block)

        # Predictions set
        pred_set = set(predictions)
        for pd_block in predictions:
            pred_set.add(pd_block)

        # Calculate correct predictions
        correct = len(gt_set.intersection(pred_set))

        # Calculate recall and precision
        stat_cov_recall = correct / len(gt_set)
        stat_cov_precision = correct / len(pred_set)

        return stat_cov_recall, stat_cov_precision
    except:
        return None, None
    
# Error Location Matching
def calculate_error_location(pred_execution, actuals):
    '''Compares the predicted and actual error locations to determine if they match.

    This function evaluates whether the last statement in the predicted execution matches 
    the last statement in the actual execution, which represents the error location.

    Arguments:
        pred_execution (list): A list of predicted statement numbers representing the execution trace.
                               The last statement in this list is considered the predicted error location.
        actuals (list): A list of ground truth statement numbers representing the execution trace.
                        The last statement in this list is considered the actual error location.

    Returns:
        int: Returns `1` if the predicted error block matches the actual error block, otherwise `0`.
        None: Returns `None` if an error occurs during execution (e.g., invalid input format).
    '''
    try:
        # Get the last element of the predicted and actual executions
        gt_error_loc = int(actuals[-1])
        pd_error_loc = int(pred_execution[-1])

        # Check if the error locations match
        if pd_error_loc == gt_error_loc: return 1
        else: return 0
    except:
        return None

# Error type Matching
def calculate_error_type(predictions, ground_truth_exception_info):
    '''Compares the predicted error type with the ground truth error type.

    This function compares the predicted error type with the ground truth error type.

    Arguments:
        predictions (str): The predicted error type.
        ground_truth_exception_info (dict or None): A dictionary containing the ground truth exception information.
    
    Returns:
        int: Returns `1` if the predicted error type matches the ground truth error type, otherwise `0`.
        None: Returns `None` if an error occurs during execution (e.g., invalid input format).
    '''
    try:
        import re
        pattern = r"TypeError"
        match = re.search(pattern, ground_truth_exception_info['class'])
        if match: 
            gt_exception_info = "TypeError"
            if predictions.lower().strip() == gt_exception_info.lower().strip(): return 1
            else: return 0
        else: 
            return 1
    except:
        return None
