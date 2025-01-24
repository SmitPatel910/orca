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
    '''Generate the ground truth execution trace with line numbers and symbol tables.

    This function processes a list of execution data, where each entry contains a `line`
    number and variable states (`var_val`).

    Arguments:
        actuals (list): A list of dictionaries, where each dictionary represents the execution
                        state of a line and contains the following keys:
                        - 'line' (str): The line number.
                        - 'var_val' (list): A list of dictionaries representing variable states.
                          Each dictionary maps variable names to their values.
                          Example: [{'line': '1', 'var_val': [{'x': 10}, {'y': 20}]}]

    Returns:
        list: A list of dictionaries, where each dictionary represents the execution trace for
              a line and contains:
              - 'line' (int): The line number.
              - 'symbol_table' (dict): A dictionary of variables and their corresponding values.

            Example:
            [
                {'line': 1, 'symbol_table': {'x': 10, 'y': 20}},
                {'line': 2, 'symbol_table': {}},
                ...
            ]
    '''
    execution_trace = []
    for line in actuals:
        block_number = line['line']
        symbol_table = {}
        # If var_val is empty, no variables exist for this line
        if len(line['var_val']) == 0:
            execution_trace.append({"line": int(block_number), "symbol_table": symbol_table})
            continue
        # Process variable states in var_val
        for each_state in line['var_val']:
            # - Access the first (and only) key in each_state, which represents the variable name.
            variable_name = list(each_state.keys())[0]
            # - Access the first (and only) value in each_state, which represents the variable value.
            variable_value = list(each_state.values())[0]
            # - Add the variable name and value to the symbol table.
            symbol_table[variable_name] = variable_value

        execution_trace.append({"line": int(block_number), "symbol_table": symbol_table})

    return execution_trace

# Exact Match accuracy
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
    
# Statement Coverage accuracy
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
        for gt_line in actuals:
            gt_set.add(gt_line)

        # Predictions set
        pred_set = set(predictions)
        for pd_line in predictions:
            pred_set.add(pd_line)

        # Calculate correct predictions
        correct = len(gt_set.intersection(pred_set))

        # Calculate recall and precision
        stat_cov_recall = correct / len(gt_set)
        stat_cov_precision = correct / len(pred_set)

        return stat_cov_recall, stat_cov_precision
    except:
        return None, None

# Prefix Match accuracy
def calculate_prefix_match(predictions, actuals):
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

# Symbol table accuracy
def calculate_symbol_table_accuracy(pred_symbol_table, actuals):
    '''
    Calculate the accuracy of the predicted symbol table against the ground truth symbol table.

    This function compares the predicted symbol table (`pred_symbol_table`) to the actual execution trace (`actuals`)
    to determine how accurately their values match.

    Arguments:
        pred_symbol_table (list): A list of dictionaries representing the predicted symbol table for each line/block.
                            Example: [{'line': 1, 'symbol_table': {'x': '1', 'y': "'hello'"}}, ...]
        actuals (list): A list of dictionaries representing the ground truth execution trace for each line/block.
                            Example: [{'line': '1', 'var_val': [{'x': 10}, {'y': 20}]}]

    Returns:
        float or None: The accuracy of the predicted symbol table as a ratio of correct matches to total matches.
        Returns `None` if no comparisons can be made.
    '''
    try:
        # Convert the actuals to the same format as the predicted symbol table
        # From: [{'line': '1', 'var_val': [{'x': 10}, {'y': 20}]}]
        # To: [{'line': 1, 'symbol_table': {'x': 10, 'y': 20}}]
        actuals = get_gt_execution_trace(actuals)
        gt_symbol_table = actuals

        correct_match = 0
        incorrect_match = 0

        # Iterate over the prediction symbol table (all the lines)
        for index, pd_line in enumerate(pred_symbol_table):

            # Check if the index is out of bounds
            if index >= len(gt_symbol_table): break

            # If the line numbers do not match, skip the comparison
            if not pd_line['line'] == actuals[index]['line']: continue
            # If the predicted symbol table is empty, skip the comparison
            if pd_line['symbol_table'] == "": continue

            pred_symbol_table = pd_line['symbol_table']
            gt_symbol_table = actuals[index]['symbol_table']

            # Check all the variables values for the current line
            for key in pred_symbol_table.keys():
                # If the predicted variable is not in the ground truth, skip the comparison
                if not key in gt_symbol_table: continue

                gt = gt_symbol_table[key]
                pred_value = pred_symbol_table[key]

                # Remove quotes from the ground truth value
                if gt.startswith('"') or gt.startswith("'"):    gt = gt[1:]
                if gt.endswith('"') or gt.endswith("'"):   gt = gt[:-1]

                # Check that prediction made by the model is actually a AST node (valid value)
                pred_value = eval(pred_value)

                if isinstance(pred_value, list):
                    # Convert the list to a string of 'list' to compare with the ground truth
                    # e.g. From: [1, 2, 3], To: '['1', '2', '3']'
                    pred_value = [f'{item}' for item in pred_value]
                    pred_value = str(pred_value)
                else:
                    pred_value = str(pred_value)
                
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
