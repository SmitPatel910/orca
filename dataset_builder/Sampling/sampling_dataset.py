import random

def select_instances(prob_count_list, total_count):
    '''Distribute instances across problems based on available counts and total limit.

    This function selects a fixed number of instances (`total_count`) from a list of problems,
    ensuring even distribution while handling any remaining quota randomly.

    Args:
        prob_count_list (list): A list of tuples where each tuple contains:
            - prob (str): The problem ID.
            - count (int): The number of available instances for the problem.
        total_count (int): The total number of instances to select across all problems.

    Returns:
        dict: A mapping of problem IDs to the number of selected instances.
    '''

    selected_instances = []
    
    # Calculate the number of instances to select per problem
    instances_per_category = total_count // len(prob_count_list)
    
    # Distribute the instances evenly across problems
    for prob, count in prob_count_list:
        # Select the minimum of available instances or the calculated limit
        selected_instances.extend([prob] * min(instances_per_category, count))
    
    # Calculate the remaining instances to be distributed
    remaining_count = total_count - len(selected_instances)
    
    if remaining_count > 0:
        # Gather remaining instances from problems with extra capacity
        remaining_instances = []
        for prob, count in prob_count_list:
            remaining_instances.extend([prob] * max(0, count - instances_per_category))
        # Shuffle the remaining instances to ensure random selection
        random.shuffle(remaining_instances)
        # Add remaining instances to the selected list
        selected_instances.extend(remaining_instances[:remaining_count])
    
    # Convert the list of selected instances into a mapping (problem ID -> selected count)
    instance_map = {}
    for prob in selected_instances:
        if prob not in instance_map:
            instance_map[prob] = 0
        instance_map[prob] += 1

    return instance_map

def select_sub_data(dataset, instance_map, prob_sub_mapping):
    '''Select a subset of data from the dataset based on instance mapping.

    This function selects a specified number of submissions for each problem based on the 
    instance mapping, shuffling the available submissions for randomness.

    Args:
        dataset (dict): The dataset containing problems and their submissions.
        instance_map (dict): A mapping of problem IDs to the number of submissions to select.
        prob_sub_mapping (dict): A mapping of problem IDs to their corresponding submission IDs.

    Returns:
        dict: A new dataset containing only the selected submissions.
    '''
    selected_data = {}
    for prob, count in instance_map.items():
        selected_data[prob] = {}
        available_subs = prob_sub_mapping[prob]
        random.shuffle(available_subs)
        temp = {}
        for sub in available_subs[:count]:
            temp[sub] = dataset[prob][sub]
        selected_data[prob] = temp
    return selected_data

def analyze_the_dataset(dataset):
    '''Analyze a dataset to count submissions per problem and map problems to their submissions.

    This function processes a dataset to determine the number of submissions for each problem 
    and creates a mapping of problem IDs to their corresponding submission IDs.

    Args:
        dataset (dict): A dataset containing problems and their submissions.
            
    Returns:
        tuple: A tuple containing:
            - prob_count_list (list): A list of tuples, each containing a problem ID and 
              the number of submissions for that problem.
            - prob_sub_mapping (dict): A dictionary mapping each problem ID to a list of 
              its submission IDs.
    '''
    # Initialize a list to store the problem ID and submission count
    prob_count_list = []

    # Initialize a dictionary to map problem IDs to submission IDs
    prob_sub_mapping = {}

    # Iterate through each problem in the dataset
    for prob in dataset:
        count = 0 # Initialize submission count for the current problem
        temp = []
        
        # Iterate through submissions for the current problem
        for sub in dataset[prob]:
            temp.append(sub) # Add submission ID to the temporary list
            count += 1  # Increment the submission count
        
        # If there are submissions for the problem, update mappings and counts
        if count > 0:
            prob_sub_mapping[prob] = temp  # Map the problem ID to its submission IDs
            prob_count_list.append((prob, count)) # Add the problem and submission count to the list
    
    # Return the problem count list and problem-to-submission mapping
    return prob_count_list, prob_sub_mapping

def merge_dataset(dataset1, dataset2):
    '''Merge two datasets into a single dataset, ensuring all entries have exception information.

    This function combines two datasets by iterating through each problem ID and submission ID,
    ensuring that each submission includes an `exception_info` field (set to `None` if missing).

    Args:
        dataset1 (dict): The first dataset to merge.
        dataset2 (dict): The second dataset to merge.

    Returns:
        dict: A merged dataset containing all problem and submission entries from both input datasets.
    '''
    # Initialize the merged dataset
    merged_dataset = {}

    # Merge entries from the first dataset
    for prob_id in dataset1:
        for sub_id in dataset1[prob_id]:
            obj = dataset1[prob_id][sub_id]
            
            # Ensure 'exception_info' field is present (set to None if missing)
            if 'exception_info' not in obj:
                obj['exception_info'] = None
            
            # Add the problem and submission to the merged dataset
            if prob_id not in merged_dataset:    merged_dataset[prob_id] = {}
            if sub_id not in merged_dataset[prob_id]:    merged_dataset[prob_id][sub_id] = {}
            merged_dataset[prob_id][sub_id] = obj

    # Merge entries from the second dataset
    for prob_id in dataset2:
        for sub_id in dataset2[prob_id]:
            obj = dataset2[prob_id][sub_id]

            # Ensure 'exception_info' field is present (set to None if missing)
            if 'exception_info' not in obj:
                obj['exception_info'] = None
            
            # Add the problem and submission to the merged dataset
            if prob_id not in merged_dataset:    merged_dataset[prob_id] = {}
            if sub_id not in merged_dataset[prob_id]:    merged_dataset[prob_id][sub_id] = {}
            merged_dataset[prob_id][sub_id] = obj

    # Return the merged dataset
    return merged_dataset

def main(buggy_dataset, non_buggy_dataset):
    '''Process and merge buggy and non-buggy datasets by selecting a subset of instances.

    This function analyzes the buggy and non-buggy datasets, selects a specified number 
    of instances from each dataset, and merges the selected subsets into a combined dataset.

    Args:
        buggy_dataset (dict): The dataset containing buggy code instances.
            Format: {problem_id: {submission_id: {data}}, ...}
        non_buggy_dataset (dict): The dataset containing non-buggy code instances.
            Format: {problem_id: {submission_id: {data}}, ...}

    Returns:
        dict: A merged dataset containing selected buggy and non-buggy instances.
            Format: {problem_id: {submission_id: {data}}, ...}
    '''
    # Analyze the buggy and non-buggy datasets to get problem counts and valid mappings
    buggy_prob_count_list, valid_buggy_prob_sub_mapping = analyze_the_dataset(buggy_dataset)
    non_buggy_prob_count_list, valid_non_buggy_prob_sub_mapping = analyze_the_dataset(non_buggy_dataset)

    # Define the total count of instances to select from each dataset
    total_count = 374
    
    # Select a subset of buggy and non-buggy instances
    selected_buggy_instances_mapping = select_instances(buggy_prob_count_list, total_count)
    selected_nonbuggy_instances_mapping = select_instances(non_buggy_prob_count_list, total_count)

    # Retrieve the selected subset data from the buggy and non-buggy datasets
    selected_buggy_data = select_sub_data(buggy_dataset, selected_buggy_instances_mapping, valid_buggy_prob_sub_mapping)
    selected_non_buggy_data = select_sub_data(non_buggy_dataset, selected_nonbuggy_instances_mapping, valid_non_buggy_prob_sub_mapping)

    # Merge the selected subsets of buggy and non-buggy data into one dataset
    merged_data = merge_dataset(selected_non_buggy_data, selected_buggy_data)

    return merged_data
