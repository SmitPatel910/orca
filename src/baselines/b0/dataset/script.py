import json

with open('fixeval_cfg.json', 'r') as file:
    data = json.load(file)
    
def flatten_data(data):
    falttened_data = {}
    for key in data.keys():
        for sub in data[key]:
            falttened_data[f'{key}_{sub}'] = data[key][sub]
    return falttened_data

final_data = flatten_data(data)

with open('fixeval_cfg_codexe.json', 'w') as file:
    json.dump(final_data, file)