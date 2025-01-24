import json
from pathlib import Path

# Setting up the paths for the dataset and the temporary dataset directory.
script_directory = Path(__file__).resolve()
base_directory = script_directory.parents[3]

# Function to print the results
def print_results(is_complete, total, buggy_count, non_buggy_count, ErrorLocation, tp, fp, fn, tn, EM, PRE_R, PRE_P, COV_R, COV_P):
    print(f"Total Instances: {total}")
    print(f"Buggy Instances: {buggy_count}")
    print(f"Non-Buggy Instances: {non_buggy_count}")
    
    if is_complete:
        print("\n============== RQ1 ==============")
    else:
        print("\n============== RQ2 ==============")
    print("Table 1 - Error Localization")
    print(f"Error Localization: {100 * (ErrorLocation/buggy_count):.2f}")
    
    print("\nTable 2 - Error Detection")
    print(f"True Positive Instances: {tp}")
    print(f"False Positive Instances: {fp}")
    print(f"False Negative Instances: {fn}")
    print(f"True Negative Instances: {tn}")
    
    print(f"\nTrue Positive Rate: {100 * (tp/buggy_count):.2f}")
    print(f"False Positive Rate: {100 * (fp/non_buggy_count):.2f}")
    print(f"False Negative Rate: {100 * (fn/buggy_count):.2f}")
    print(f"True Negative Rate: {100 * (tn/non_buggy_count):.2f}")
    
    print(f"\nAccuracy: {100 * ((tp + tn)/(buggy_count + non_buggy_count)):.2f}")

    print("\n============== RQ3 ==============")
    print(f"Exact Match: {100 * (EM/total):.2f}")
    print(f"\nPrefix Recall: {100 * (PRE_R/total):.2f}")
    print(f"Prefix Precision: {100 * (PRE_P/total):.2f}")
    print(f"\nStatement Cov. Recall: {100 * (COV_R/total):.2f}")
    print(f"Statement Cov. Precision: {100 * (COV_P/total):.2f}")

# Function to process the Accuracy data
def process_data(is_complete, dataset, response_cache):
    ErrorLocation = 0 # Error Localization Accuracy
    tp = 0 # True Positive
    fp = 0 # False Positive
    fn = 0 # False Negative
    tn = 0 # True Negative
    EM = 0 # Exact Match
    COV_R = 0 # Statement Coverage Recall
    COV_P = 0 # Statement Coverage Precision
    PRE_R = 0 # Prefix Match Recall
    PRE_P = 0 # Prefix Match Precision
    
    buggy_count = 0 # Number of buggy instances
    non_buggy_count = 0 # Number of non-buggy instances

    for probID in response_cache:

        for subID in response_cache[probID]:

            ground_truth_exception_info = dataset[probID][subID]['exception_info']
            obj = response_cache[probID][subID]
            
            # Check if the instance is buggy or not
            if ground_truth_exception_info:
                buggy_count += 1
            else:
                non_buggy_count += 1

            # Check if the instance is empty
            if obj == {}: continue
            if obj['accuracy'] == {}: continue
            
            accuracy = obj['accuracy']
            
            # RQ1
            # Checking for the Error Detection (True Positive, False Positive, False Negative, True Negative)
            if accuracy['Is_Error'] != None:
                # If the instance is buggy and the model predicts it as buggy
                if ground_truth_exception_info and accuracy['Is_Error'] == True:
                    tp += 1 # True Positive
                
                # If the instance is not buggy and the model predicts it as not buggy
                elif not ground_truth_exception_info and accuracy['Is_Error'] == False:
                    tn += 1 # True Negative

                # If the instance is not buggy and the model predicts it as buggy
                elif not ground_truth_exception_info and accuracy['Is_Error'] == True:
                    fp += 1 # False Positive

                # If the instance is buggy and the model predicts it as not buggy
                elif ground_truth_exception_info and accuracy['Is_Error'] == False:
                    fn += 1 # False Negative
            
            # Checking for the Error Localization
            if ground_truth_exception_info and accuracy['ErrorLocation'] and accuracy['Is_Error'] == True:
                ErrorLocation += accuracy['ErrorLocation'] # Error Localization Accuracy
            
            # RQ2
            # Checking for the Exact Match
            if accuracy['EM'] != None:  
                EM += accuracy['EM'] # Exact Match

            # Checking for the Prefix Match 
            if accuracy['PRE'][0] != None and accuracy['PRE'][1] != None:  
                PRE_R += accuracy['PRE'][0] # Prefix Match Recall
                PRE_P += accuracy['PRE'][1] # Prefix Match Precision
            
            # Checking for the Statement Coverage
            if accuracy['COV'][0] != None and accuracy['COV'][1] != None:
                COV_R += accuracy['COV'][0] # Statement Coverage Recall
                COV_P += accuracy['COV'][1] # Statement Coverage Precision

    total = buggy_count + non_buggy_count

    # Output the results
    print_results(is_complete, total, buggy_count, non_buggy_count, ErrorLocation, tp, fp, fn, tn, EM, PRE_R, PRE_P, COV_R, COV_P)

# Function to load the dataset
def load_dataset(dataset_path):
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    return data

if __name__ == "__main__":
    # Dataset paths
    complete_code_dataset = base_directory / 'dataset' / 'fixeval_merged_cfg.json'
    incomplete_code_dataset = base_directory / 'dataset' / 'fixeval_incom_merged_cfg.json'

    # Response Directory
    response_save_dir = base_directory / 'output' / 'baseline' / 'b2'
    complete_code_res_dir = response_save_dir / 'b2_complete_fixeval.json'
    incomplete_code_res_dir = response_save_dir / 'b2_incomplete_fixeval.json'

    # Load the dataset
    print("Loading the dataset...")
    complete_code_data = load_dataset(complete_code_dataset)
    incomplete_code_data = load_dataset(incomplete_code_dataset)
    print("Loading Results...")
    complete_b2_res = load_dataset(complete_code_res_dir)
    incomplete_b2_res = load_dataset(incomplete_code_res_dir)

    # Process the data
    print("\n===================== Complete Code Results =====================")
    process_data(True, complete_code_data, complete_b2_res)
    print("\n===================== Incomplete Code Results =====================")
    process_data(False, incomplete_code_data, incomplete_b2_res)
    print()
