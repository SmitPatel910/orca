import json
import random

with open('../../dataset/ready_for_sample/fixeval_crash_cfg_entire.json', 'r') as file:
    fixeval_cfg = json.load(file)

def reset_problem_ids(data, fixeval_cfg):
    reset_data = {}

    for block_ids in data.keys():
        if len(data[block_ids]) == 0: continue
        for full_key in data[block_ids]:
            problem_id, submission_id = full_key.split('_')
            if problem_id not in reset_data:
                reset_data[problem_id] = {}
            reset_data[problem_id][submission_id] = fixeval_cfg[problem_id][submission_id]

    return reset_data

def build_dataset(fixeval_cfg):
    problem_solution_size = []
    for key in fixeval_cfg:
        solution_in_prob = len(fixeval_cfg[key])
        if solution_in_prob == 0: continue
        problem_solution_size.append(solution_in_prob)
    total_problems = len(problem_solution_size)
    total_solutions = sum(problem_solution_size)
    average_number_of_solutions_in_each_problem = total_solutions / total_problems

    dataset_sample_size = 373
    percentage_to_select = (dataset_sample_size / total_solutions)
    solutions_in_selected_problems = {}
    
    for key in fixeval_cfg:
        if len(fixeval_cfg[key]) == 0: continue
        sample_size = int(percentage_to_select * len(fixeval_cfg[key]))
        if sample_size >= 1:
            solutions_in_selected_problems[key] = sample_size
    while True:
        remaining = dataset_sample_size - sum(solutions_in_selected_problems.values())
        if remaining <= 0: break
        keys = fixeval_cfg.keys()
        random_key = random.choice(list(keys))
        if random_key not in solutions_in_selected_problems.keys():
            len_solutions = len(fixeval_cfg[random_key])
            if len_solutions == 0: continue
            range_numbers = int(len_solutions / 5)
            if not range_numbers >= 1: continue
            solutions_in_selected_problems[random_key] = random.randint(1, range_numbers)
    
    final_dataset_3 = {}
    for problem in solutions_in_selected_problems:
        number_of_sols_to_select = solutions_in_selected_problems[problem]
        final_dataset_3[problem] = {}
        # Randomly select the solutions
        solutions_dict = fixeval_cfg[problem]
        selected_solution_keys = random.sample(list(solutions_dict.keys()), number_of_sols_to_select)
        final_dataset_3[problem] = {}
        for sol_id in selected_solution_keys:
            final_dataset_3[problem][sol_id] = fixeval_cfg[problem][sol_id]

    return final_dataset_3

# get the stats
def get_stats(dataset):
    stats = {}
    frequency = {}
    count = 0
    for prob in dataset:
        for sub in dataset[prob]:
            if dataset[prob][sub] == {}: continue
            gt_length = len(dataset[prob][sub]['ground_truth_blocks'])
            if str(gt_length) not in stats.keys():
                stats[f'{gt_length}'] = []
                frequency[f'{gt_length}'] = 0
            else:
                stats[str(gt_length)].append(f'{prob}_{sub}')
                frequency[str(gt_length)] += 1
                count += 1
    return stats, frequency, count

# get stats for dataset 3
def get_stats_dataset(dataset):
    count = 0
    submission_stats = {'min': 100, 'max': 0, 'mean': 0, '0_1': 0, '1_3': 0, '3_5': 0, '5_10': 0, '10_15': 0, '15_20': 0, '20_25': 0, '25_30': 0, '30_35': 0, '35_40': 0, '40_46': 0}
    for prob in dataset:
        for sub in dataset[prob]:
            if dataset[prob][sub] == {}: continue
            gt_length = len(dataset[prob][sub]['ground_truth_blocks'])
            if gt_length < submission_stats['min']:
                submission_stats['min'] = gt_length
            if gt_length > submission_stats['max']:
                submission_stats['max'] = gt_length
            submission_stats['mean'] += gt_length
            if gt_length <= 1:
                submission_stats['0_1'] += 1
            elif gt_length <= 3:
                submission_stats['1_3'] += 1
            elif gt_length <= 5:
                submission_stats['3_5'] += 1
            elif gt_length <= 10:
                submission_stats['5_10'] += 1
            elif gt_length <= 15:
                submission_stats['10_15'] += 1
            elif gt_length <= 20:
                submission_stats['15_20'] += 1
            elif gt_length <= 25:
                submission_stats['20_25'] += 1
            elif gt_length <= 30:
                submission_stats['25_30'] += 1
            elif gt_length <= 35:
                submission_stats['30_35'] += 1
            elif gt_length <= 40:
                submission_stats['35_40'] += 1
            else:
                submission_stats['40_46'] += 1
            count += 1
    submission_stats['mean'] = submission_stats['mean'] / count
    return submission_stats, count

# Get the stats for the entire fixeval_cfg dataset
main_stats, freq, count = get_stats(fixeval_cfg)
# sorted_keys = sorted(freq.keys(), key=lambda x: (x.isdigit(), int(x) if x.isdigit() else x))
print(f"Total: {count}")
print(freq)
print()


# Sampling the Dataset by Random Distribution
fdataset = build_dataset(fixeval_cfg)
stats, count = get_stats_dataset(fdataset)
print(f"Total: {count}")
print(stats)

# Save the datasets
with open('../../dataset/fixeval_cfg.json', 'w') as file:
    json.dump(fdataset, file)