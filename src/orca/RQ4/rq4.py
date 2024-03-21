import json
from utils import get_scope

with open('dataset/fixeval_cfg.json', 'r') as file:
    dataset = json.load(file)

with open('output/output_fixeval_cfg.json', 'r') as file:
    output = json.load(file)

count = 0

type_statements = {
    'for': {"correct": 0, "incorrect": 0, "total": 0},
    'while': {"correct": 0, "incorrect": 0, "total": 0},
    'if': {"correct": 0, "incorrect": 0, "total": 0},
    'simple': {"correct": 0, "incorrect": 0, "total": 0}
}

for key in output.keys():
    for sub in output[key].keys():
        if output[key][sub]['accuracy'] == {}: continue
        EB = output[key][sub]['accuracy']['EB']
        gt_execution = dataset[key][sub]['ground_truth_execution_order']
        code = dataset[key][sub]['code']
        for_loop, while_loop, if_statement, simple_statement = get_scope(code)
        line_number = gt_execution[-1]
        type_statement = ""
        for scope in for_loop:
            if scope[0] <= line_number <= scope[1]:
                type_statement = "for"
                break
        for scope in while_loop:
            if scope[0] <= line_number <= scope[1]:
                type_statement = "while"
                break
        for scope in if_statement:
            if scope[0] <= line_number <= scope[1]:
                type_statement = "if"
                break
        for scope in simple_statement:
            if scope[0] <= line_number <= scope[1]:
                type_statement = "simple"
                break
        count += 1
        try:
            if EB == 1:
                type_statements[type_statement]["correct"] += 1
                type_statements[type_statement]["total"] += 1
            else:
                type_statements[type_statement]["incorrect"] += 1
                type_statements[type_statement]["total"] += 1
        except:
            continue

# Population Analysis
for_per = f"{100 * (type_statements['for']['total'] / count):.2f}"
while_per = f"{100 * (type_statements['while']['total'] / count):.2f}"
if_per = f"{100 * (type_statements['if']['total'] / count):.2f}"
simple_per = f"{100 * (type_statements['simple']['total'] / count):.2f}"
# Accuracy Analysis
for_pre = f"{100 * (type_statements['for']['correct'] / type_statements['for']['total']):.2f}"
while_pre = f"{100 * (type_statements['while']['correct'] / type_statements['while']['total']):.2f}"
if_pre = f"{100 * (type_statements['if']['correct'] / type_statements['if']['total']):.2f}"
simple_pre = f"{100 * (type_statements['simple']['correct'] / type_statements['simple']['total']):.2f}"

print("Total: ", count)

print()
print("Type:        FOR       WHILE       IF       SIMPLE")
print(f"Instances:   {type_statements['for']['total']}        {type_statements['while']['total']}         {type_statements['if']['total']}         {type_statements['simple']['total']} ")
print(f"Per(%):    ({(for_per)}%)   ({(while_per)}%)   ({(if_per)}%)    ({(simple_per)}%)")                                    
print('---------------------------------------------------------')
print(f"Correct:      {type_statements['for']['correct']}        {type_statements['while']['correct']}         {type_statements['if']['correct']}          {type_statements['simple']['correct']}")
print(f"Incorrect:    {type_statements['for']['incorrect']}        {type_statements['while']['incorrect']}         {type_statements['if']['incorrect']}          {type_statements['simple']['incorrect']}")
print(f"Acc(%):    ({(for_pre)}%)  ({(while_pre)}%)  ({(if_pre)}%)    ({(simple_pre)}%)")
print()