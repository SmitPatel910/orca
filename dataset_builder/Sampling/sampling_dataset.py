import random

def select_instances(prob_count_list, total_count):
    selected_instances = []
    instances_per_category = total_count // len(prob_count_list)
    
    for prob, count in prob_count_list:
        selected_instances.extend([prob] * min(instances_per_category, count))
    
    remaining_count = total_count - len(selected_instances)
    
    if remaining_count > 0:
        remaining_instances = []
        for prob, count in prob_count_list:
            remaining_instances.extend([prob] * max(0, count - instances_per_category))
        
        random.shuffle(remaining_instances)
        selected_instances.extend(remaining_instances[:remaining_count])
    
    instance_map = {}
    for prob in selected_instances:
        if prob not in instance_map:
            instance_map[prob] = 0
        instance_map[prob] += 1

    return instance_map

def select_sub_data(dataset, instance_map, prob_sub_mapping):
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
    prob_count_list = []
    prob_sub_mapping = {}

    for prob in dataset:
        count = 0; temp = []
        for sub in dataset[prob]:
            temp.append(sub)
            count += 1
        if count > 0:
            prob_sub_mapping[prob] = temp
            prob_count_list.append((prob, count))
    
    return prob_count_list, prob_sub_mapping

def merge_dataset(dataset1, dataset2):
    merged_dataset = {}
    for prob_id in dataset1:
        for sub_id in dataset1[prob_id]:
            obj = dataset1[prob_id][sub_id]
            if 'exception_info' not in obj:
                obj['exception_info'] = None
            if prob_id not in merged_dataset:    merged_dataset[prob_id] = {}
            if sub_id not in merged_dataset[prob_id]:    merged_dataset[prob_id][sub_id] = {}
            merged_dataset[prob_id][sub_id] = obj

    for prob_id in dataset2:
        for sub_id in dataset2[prob_id]:
            obj = dataset2[prob_id][sub_id]
            if 'exception_info' not in obj:
                obj['exception_info'] = None
            if prob_id not in merged_dataset:    merged_dataset[prob_id] = {}
            if sub_id not in merged_dataset[prob_id]:    merged_dataset[prob_id][sub_id] = {}
            merged_dataset[prob_id][sub_id] = obj

    return merged_dataset

def main(buggy_dataset, non_buggy_dataset):

    buggy_prob_count_list, valid_buggy_prob_sub_mapping = analyze_the_dataset(buggy_dataset)
    non_buggy_prob_count_list, valid_non_buggy_prob_sub_mapping = analyze_the_dataset(non_buggy_dataset)

    # Sort list descending by count
    total_count = 374
    selected_buggy_instances_mapping = select_instances(buggy_prob_count_list, total_count)
    selected_nonbuggy_instances_mapping = select_instances(non_buggy_prob_count_list, total_count)

    selected_buggy_data = select_sub_data(buggy_dataset, selected_buggy_instances_mapping, valid_buggy_prob_sub_mapping)
    selected_non_buggy_data = select_sub_data(non_buggy_dataset, selected_nonbuggy_instances_mapping, valid_non_buggy_prob_sub_mapping)

    merged_data = merge_dataset(selected_non_buggy_data, selected_buggy_data)
    return merged_data
