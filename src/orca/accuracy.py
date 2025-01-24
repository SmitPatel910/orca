def get_gt_execution_order(actuals):
    '''Extract the ground truth execution order from a list of execution data.

    It extracts block numbers, converts them to integers, and returns them as a list in the order they appear.

    Arguments:
        actuals (list): A list of dictionaries, where each dictionary contains a `block` 
                        key with a block number as its value.
                        Example: [{'block': '1'}, {'block': '2'}, ...]

    Returns:
        list: A list of integers representing the execution order of blocks.
              Example: [1, 2, 3, ...]
    '''
    execution_order = []
    for line in actuals:
        block_number = line['block']
        execution_order.append(int(block_number))
    return execution_order

def get_gt_execution_trace(actuals):
    '''Generate the ground truth execution trace with block numbers and symbol tables.

    This function processes a list of execution data, where each entry contains a `block`
    number and variable states.

    Arguments:
        actuals (list): A list of dictionaries, where each dictionary represents the execution
                        state of a line and contains the following keys:
                        - 'block' (str): The line number.
                        - 'state' (list): A list of dictionaries representing variable states.
                          Each dictionary maps variable names to their values.
                          Example: [{'block_id': '1', 'symbol_table': [{'x': 10}, {'y': 20}]}]

    Returns:
        list: A list of dictionaries, where each dictionary represents the execution trace for
              a line and contains:
              - 'block_id' (int): The block number.
              - 'symbol_table' (dict): A dictionary of variables and their corresponding values.

            Example:
            [
                {'block': 1, 'symbol_table': {'x': 10, 'y': 20}},
                {'block': 2, 'symbol_table': {}},
                ...
            ]
    '''
    execution_trace = []
    for line in actuals:
        block_number = line['block']
        symbol_table = {}
        # if the state is empty, no variables exist for this block
        if line['state'] == []:
            execution_trace.append({"block_id": int(block_number), "symbol_table": symbol_table})
            continue
        # Process each variable state and add it to the symbol table
        for each_state in line['state']:
            # - Access the first (and only) key in each_state, which represents the variable name.
            variable_name = list(each_state.keys())[0]
            # - Access the first (and only) value in each_state, which represents the variable value.
            variable_value = list(each_state.values())[0]
            # - Add the variable name and value to the symbol table.
            symbol_table[variable_name] = variable_value
            
        execution_trace.append({"block_id": int(block_number), "symbol_table": symbol_table})
    return execution_trace

# Exact Match Accuracy
def calculate_exact_match_accuracy(predictions, actuals):
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
    '''
    Calculate the control flow accuracy between predicted and actual execution traces.

    This function evaluates the transition accuracy between consecutive blocks 
    in the predicted and actual execution traces. It calculates:
        - Recall: Fraction of actual transitions correctly predicted.
        - Precision: Fraction of predicted transitions that are correct.

    Args:
        predictions (list): A list of predicted block executions.
        actuals (list): A list of ground truth block executions.

    Returns:
        tuple: A tuple containing:
            - control_flow_recall (float or None): Recall of control flow transitions.
            - control_flow_precision (float or None): Precision of control flow transitions.
            If there are no transitions or an exception occurs, returns (None, None).
    '''
    try:
        # Extract the ground truth execution order
        actuals = get_gt_execution_order(actuals)

        # Return None if either list is empty
        if len(actuals) == 0: 
            return None, None
        if len(predictions) == 0: 
            return None, None

        correct = 0

        # If there is only one block in each list then no transitions are possible
        if len(actuals) == 1 and len(predictions) == 1:
            if predictions[0] == actuals[0]: 
                return 1, 1
            else: 
                return 0, 0

        # Create sets of block transitions for predictions and actuals
        gt_block_transition = set()
        pd_block_transition = set()

        # Add transitions between consecutive blocks to the sets
        for i in range(len(actuals) - 1):
            gt_block_transition.add((actuals[i], actuals[i+1]))
        for i in range(len(predictions) - 1):
            pd_block_transition.add((predictions[i], predictions[i+1]))

        # Calculate the number of correct transitions
        correct = len(pd_block_transition.intersection(gt_block_transition))

        # Calculate recall and precision
        control_flow_recall = correct / len(gt_block_transition)
        control_flow_precision = correct / len(pd_block_transition)

        return control_flow_recall, control_flow_precision
    except:
        return None, None

# Block Coverage: Recall, Precision
def calculate_block_coverage(predictions, actuals):
    '''Calculates the recall and precision of block coverage between predicted and actual executions.

    Arguments:
        predictions (list): A list of predicted traversed blocks.
        actuals (list): A list of ground truth executed blocks.

    Returns:
        tuple: A tuple containing:
            - block_cov_recall (float or None): The recall of block coverage, calculated as:
              (correctly predicted blocks) / (total ground truth blocks).
              Returns `None` if `actuals` is empty or an error occurs.

            - block_cov_precision (float or None): The precision of block coverage, calculated as:
                (correctly predicted blocks) / (total predicted blocks).
                Returns `None` if `predictions` is empty or an error occurs.
    '''
    try:
        # Extract the ground truth execution order
        actuals = get_gt_execution_order(actuals)

        # Return None if either list is empty
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
        block_cov_recall = correct / len(gt_set)
        block_cov_precision = correct / len(pred_set)

        return block_cov_recall, block_cov_precision
    except:
        return None, None

# Prefix Match (First wrong prediction) Recall, Precision
def calculate_prefix_accuracy(predictions, actuals):
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
        # Extract the ground truth execution order
        actuals = get_gt_execution_order(actuals)

        # Return None if either list is empty
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

# Symbol table accuracy
def calculate_symbol_table_accuracy(pred_symbol_table, actuals):
    '''
    Calculate the accuracy of the predicted symbol table against the ground truth symbol table.

    This function compares the predicted symbol table (`pred_symbol_table`) to the actual execution trace (`actuals`)
    to determine how accurately their values match.

    Arguments:
        pred_symbol_table (list): A list of dictionaries representing the predicted symbol table for each line/block.
                            Example: [{'block': 1, 'symbol_table': {'x': '1', 'y': "'hello'"}}, ...]
        actuals (list): A list of dictionaries representing the ground truth execution trace for each line/block.
                            Example: [{'block': '1', 'state': [{'x': 10}, {'y': 20}]}]

    Returns:
        float or None: The accuracy of the predicted symbol table as a ratio of correct matches to total matches.
        Returns `None` if no comparisons can be made.
    '''

    try:
        # Convert the actuals to the same format as the predicted symbol table
        # From: [{'block': '1', 'state': [{'x': 10}, {'y': 20}]}]
        # To: [{'block_id': 1, 'symbol_table': {'x': 10, 'y': 20}}, ...]
        actuals = get_gt_execution_trace(actuals)
        pred_block_id_symbol_table = pred_symbol_table

        correct_match = 0
        incorrect_match = 0

        # Iterate over the prediction symbol table (all the blocks)
        for index, pd_block in enumerate(pred_block_id_symbol_table):
            # Check if the index is out of bounds
            if index >= len(actuals): break

            # If Block ID does not match, skip to the comparison
            if not pd_block['block_id'] == actuals[index]['block_id']: continue
            # If the symbol table is empty, skip to the comparison
            if pd_block['symbol_table'] == "": continue

            pred_symbol_table = pd_block['symbol_table']
            gt_symbol_table = actuals[index]['symbol_table']

            # Check all the variables values for the current block
            for key in pred_symbol_table.keys():
                # If the predicted variable is not in the ground truth, skip the comparison
                if not key in gt_symbol_table: continue

                gt = gt_symbol_table[key]
                pred_value = pred_symbol_table[key][0]

                # Remove quotes from the ground truth value
                if gt.startswith('"') or gt.startswith("'"):    gt = gt[1:]
                if gt.endswith('"') or gt.endswith("'"):   gt = gt[:-1]
                
                gt = str(gt).strip()
                pred_value = str(pred_value).strip()

                # Check if the predicted value matches the ground truth value
                if pred_value == gt:
                    correct_match += 1
                else:
                    incorrect_match += 1
        
        # Calculate the accuracy
        if correct_match + incorrect_match == 0: return None
        accuracy  = correct_match / (correct_match + incorrect_match)
        return accuracy
    except:
        return None

# Error Block Location accuracy
def calculate_error_block_accuracy(predictions, actuals):
    '''Compares the predicted and actual error locations to determine if they match.

    This function evaluates whether the last block in the predicted execution matches 
    the last block in the actual execution, which represents the error location.

    Arguments:
        pred_execution (list): A list of predicted block numbers representing the execution trace.
                               The last block in this list is considered the predicted error location.
        actuals (list): A list of ground truth block numbers representing the execution trace.
                        The last block in this list is considered the actual error location.

    Returns:
        int: Returns `1` if the predicted error block matches the actual error block, otherwise `0`.
        None: Returns `None` if an error occurs during execution (e.g., invalid input format).
    '''
    try:
        # Extract the ground truth execution order
        actuals = get_gt_execution_order(actuals)
        
        # Get the last element of the predicted and actual executions
        gt_error_block = int(actuals[-1])
        pd_error_block = int(predictions)

        # Check if the error locations match
        if pd_error_block == gt_error_block: return 1
        else: return 0
    except:
        return None

# Error type accuracy
def calculate_error_type_accuracy(predictions, ground_truth_exception_info):
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
        match = re.search(pattern, ground_truth_exception_info)
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
    '''Calculates the recall and precision of statement coverage between predicted and actual executions. Logic is similar to block coverage.
        If block coverage is 1 means all the statements from that blocks are covered and vice versa.

    Arguments:
        predictions (list): A list of predicted executed statements.
        actuals (list): A list of ground truth executed statements.

    Returns:
        tuple: A tuple containing:
            - statement_recall (float or None): The recall of statement coverage, calculated as:
              (correctly predicted statements) / (total ground truth statements).
              Returns `None` if `actuals` is empty or an error occurs.

            - statement_precision (float or None): The precision of statement coverage, calculated as:
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
        statement_recall = correct / len(gt_set)
        statement_precision = correct / len(pred_set)

        return statement_recall, statement_precision
    except:
        return None, None
    
# Statement Level PreFix
def get_statement_prefix(predictions, actuals):
    '''Calculates the recall and precision of statement coverage between predicted and actual executions. Logic is similar to block coverage.
        If block coverage is 1 means all the statements from that blocks are covered and vice versa.

    Arguments:
        predictions (list): A list of predicted executed statements.
        actuals (list): A list of ground truth executed statements.

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
        # Return None if either list is empty
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
