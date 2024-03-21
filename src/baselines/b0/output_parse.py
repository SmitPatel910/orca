import json

with open('output/fixeval_codeExecutor.json', 'r') as file:
    pred_codeExe_fixeval = json.load(file)

with open('dataset/fixeval_final.json', 'r') as file:
    finaldata = json.load(file)

# Parse the CodeExecutor Prediction
def parse_the_prediction(prediction_data):
    pred_exe_symbol_table = {}

    for id, prob_sub in enumerate(prediction_data.keys()):
        if not prob_sub in pred_exe_symbol_table:   pred_exe_symbol_table[prob_sub] = {}
        code_executor_pred = pred_codeExe_fixeval[int(id)]
        extracted_line_numbers = []
        line_segments = code_executor_pred.split("<line>")
        prob_sub_dict = []
        for segment in line_segments:
            if not segment.strip(): continue
            parts = segment.split(">")
            if len(parts) > 1:
                line_number_str = parts[0].replace('<', '').strip()
                try:
                    line_number = int(line_number_str)
                    extracted_line_numbers.append(line_number+1)
                except ValueError:
                    continue
            if len(segment.split("<state>")) != 2: continue
            # Get the content from <state> and </state> 
            t1 = segment.split("<state>")[1].strip()
            t2 = t1.split("</state>")[0].strip()
            # Filter out the empty strings --> No Prediction
            if not t2: continue
            # Get the content from <dictsep>
            t3 = t2.split("<dictsep>")
            if not t3: continue
            # Get the key-value pairs
            temp_dict = {}
            for key_value in t3:
                key_value = key_value.strip()
                try:
                    key = key_value.split(":")[0].strip()
                    value = key_value.split(":")[1].strip()
                    temp_dict[key] = value
                except:
                    continue
            try:
                temp_dict = str(temp_dict)
                temp_dict = eval(temp_dict)
            except Exception as e:
                print(e)
                continue
            prob_sub_dict.append({"line" : line_number+1, "symbol_table" : temp_dict})
        
        pred_exe_symbol_table[prob_sub]["symbol_table"] = prob_sub_dict
        pred_exe_symbol_table[prob_sub]["execution_order"] = extracted_line_numbers

    return pred_exe_symbol_table

# Get the parsed prediction
parsed_prediction = parse_the_prediction(finaldata)

with open('output/parsed_fixeval_pred_codeExe.json', 'w') as file:
    json.dump(parsed_prediction, file, indent=4)
