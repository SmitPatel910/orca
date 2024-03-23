import json
from utils import analyze_code, remove_comments_and_blank_lines, check_code_conditions, filter_code_based_on_input_lines
from variable_locator import caller_function
from tqdm import tqdm

with open ('../dataset/structured_fixeval_dataset.json', 'r') as f:
    structured_data = json.load(f)

total_count = 0
false_count = 0
true_count = 0

filtered_data = {}

# Filter Dataset based on the loops, method calls, and other conditions
for item in tqdm(structured_data):
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

# Filtering dataset based on problem ids
h_data = filtered_data
# Get the Input variables line from the code
variable_locations = caller_function(h_data)
# Filter the dataset based on the input variables location
final_dataset, true_count = filter_code_based_on_input_lines(variable_locations)
with open('../dataset/filtered_fixeval_dataset.json', 'w') as f:
    json.dump(final_dataset, f, indent=4)
