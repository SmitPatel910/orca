import json
from pathlib import Path

# Setting up the paths for the dataset and the temporary dataset directory.
script_directory = Path(__file__).resolve()
base_directory = script_directory.parents[3]

def print_results(is_complete, count, buggy_count, non_buggy_count, ErrorLocation, tp, fp, fn, tn, EM, PRE_R, PRE_P, COV_R, COV_P):
    print(f"Total Instances: {count}")
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
    print(f"Exact Match: {100 * (EM/count):.2f}")
    print(f"\nPrefix Recall: {100 * (PRE_R/count):.2f}")
    print(f"Prefix Precision: {100 * (PRE_P/count):.2f}")
    print(f"\nStatement Cov. Recall: {100 * (COV_R/count):.2f}")
    print(f"Statement Cov. Precision: {100 * (COV_P/count):.2f}")

def process_data(is_complete, dataset, response_cache):
    ErrorLocation = 0
    tp = 0
    fp = 0
    fn = 0
    tn = 0
    EM = 0
    COV_R = 0
    COV_P = 0
    PRE_R = 0
    PRE_P = 0
    count = 0
    buggy_count = 0
    non_buggy_count = 0

    for probID in response_cache:

        for subID in response_cache[probID]:

            exception_info = dataset[probID][subID]['exception_info']
            obj = response_cache[probID][subID]
            
            if exception_info:
                buggy_count += 1
            else:
                non_buggy_count += 1

            count += 1
            if obj == {}: continue
            if obj['accuracy'] == {}: continue
            
            accuracy = obj['accuracy']
            
            # RQ1
            if accuracy['Is_Error'] != None:
                if exception_info and accuracy['Is_Error'] == True:
                    tp += 1
                elif not exception_info and accuracy['Is_Error'] == False:
                    tn += 1
                elif not exception_info and accuracy['Is_Error'] == True:
                    fp += 1
                elif exception_info and accuracy['Is_Error'] == False:
                    fn += 1
            
            if exception_info and accuracy['ErrorLocation'] and accuracy['Is_Error'] == True:
                ErrorLocation += accuracy['ErrorLocation']
            
            # RQ2
            if accuracy['EM'] != None:  
                EM += accuracy['EM']
            if accuracy['PRE'][0] != None and accuracy['PRE'][1] != None:  
                PRE_R += accuracy['PRE'][0]; PRE_P += accuracy['PRE'][1]
            if accuracy['COV'][0] != None and accuracy['COV'][1] != None:  
                COV_R += accuracy['COV'][0]; COV_P += accuracy['COV'][1]

    total = buggy_count + non_buggy_count

    # Output the results
    print_results(is_complete, total, buggy_count, non_buggy_count, ErrorLocation, tp, fp, fn, tn, EM, PRE_R, PRE_P, COV_R, COV_P)

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