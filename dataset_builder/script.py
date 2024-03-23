import json
from orca.utils import analyze_code, remove_comments_and_blank_lines, check_code_conditions, filter_code_based_on_input_lines
from variable_locator import caller_function
with open ('../dataset/structured_fixeval_dataset.json', 'r') as f:
    structured_data = json.load(f)

total_count = 0
false_count = 0
true_count = 0

filtered_data = {}

# Filter Dataset based on the loops, method calls, and other conditions
for item in structured_data:
    if item not in filtered_data:
        filtered_data[item] = {} 
    for submission in structured_data[item]:
        total_count += 1
        try:
            submission_block = structured_data[item][submission]
            code = submission_block['code']
            filtered_code = remove_comments_and_blank_lines(code)
            functions_class = submission_block['functions_class']
            functions_standalone = submission_block['functions_standalone']
            verdict = submission_block['verdict']

            analyzer = analyze_code(code)
            result = check_code_conditions(analyzer)
            if result:
                filtered_data[item][submission] = {'code': filtered_code, 'functions_class': functions_class, 'functions_standalone': functions_standalone, 'verdict': verdict} 
                true_count += 1
        except Exception as e:
            false_count += 1
            pass
print(f"Total Instances in Structured Data: {total_count}")

# Filtering dataset based on problem ids
h_data = filtered_data
with open('../dataset/previous_work_dataset.json', 'r') as f:
    s_data = json.load(f)
   
collected_problems = {}
for key in h_data.keys():
    if key in s_data:
        collected_problems[key] = {}

total_count_brefore_filter = true_count
problem_submission_count = 0
false_count = 0
for key in collected_problems.keys():
    for submission in h_data[key]:
        try:
            submission_block = h_data[key][submission]
            code = submission_block['code']
            filtered_code = remove_comments_and_blank_lines(code)
            functions_class = submission_block['functions_class']
            functions_standalone = submission_block['functions_standalone']
            verdict = submission_block['verdict']
            collected_problems[key][submission] = {'code': filtered_code, 'functions_class': functions_class, 'functions_standalone': functions_standalone, 'verdict': verdict} 
            problem_submission_count += 1
        except Exception as e:
            false_count += 1
            pass

# Get the Input variables line from the code
variable_locations = caller_function(collected_problems)
# Filter the dataset based on the input variables location
final_dataset, true_count = filter_code_based_on_input_lines(variable_locations)
print(f"Total: {problem_submission_count}, True: {true_count}")

with open('../dataset/other/filtered_fixeval_dataset.json', 'w') as f:
    json.dump(final_dataset, f, indent=4)

