'''
References:

This code is based on the baseline implementation from the following repository:

[CodeExecutor](https://github.com/microsoft/CodeBERT/blob/master/CodeExecutor/pretrain/dataset.py)
'''

import json
import pickle
from pathlib import Path
import re
from tqdm import tqdm
import torch
from torch.utils.data import Dataset

class InputFeatures(object):
    def __init__(self, id, code_tokens):
        self.id = id
        self.code_tokens = code_tokens

def indent_dedent(code, tokenizer):
    indented_code = ""
    lines = code.split('\n')
    current_num_white_spaces = 0
    prev_num_white_spaces = 0

    for line_number, line in enumerate(lines):
        line_number_token = f"<{line_number}>"
        indented_code += line_number_token + " "
        current_num_white_spaces = len(re.match(r'^\s*', line).group(0))
        
        if current_num_white_spaces > prev_num_white_spaces:
            indented_code += "<indent> "
            prev_num_white_spaces = current_num_white_spaces
        elif current_num_white_spaces < prev_num_white_spaces:
            diff = prev_num_white_spaces - current_num_white_spaces
            for temp in range(diff // 4):
                indented_code += "<dedent> "
            prev_num_white_spaces = current_num_white_spaces
        line = line.lstrip()
        indented_code += line + "\n"
        
    code_tokens = tokenizer.tokenize(indented_code)

    return code_tokens

def convert_examples_to_features(js, tokenizer):
    id = js["id"]
    code_tokens = indent_dedent(js["code"], tokenizer)
    return InputFeatures(id, code_tokens)

class CodeCoverageDataset(Dataset):
    def __init__(self, tokenizer, dataPath, args,logger):
        self.args = args
        self.tokenizer = tokenizer
        self.examples = []
        error_num = 0
   
        with open(dataPath, "r") as json_file:
            dataset = json.load(json_file)

        for i, index in enumerate(dataset):
            if len(dataset[index]['code']) != 0: 
                js = {
                    "id": index,
                    "code": dataset[index]["code"]
                }
                try:
                    features = convert_examples_to_features(js, tokenizer)
                    self.examples.append(features)
                except Exception as e:
                    error_num += 1
                    print(f"Error processing example: {str(e)}")

            
        logger.warning(f"Num examples = {len(self.examples)}")
        logger.warning(f"Error num = {error_num}")

    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, item): 
        js = self.examples[item]
        
        max_source_size = self.args.max_source_size
        max_target_size = self.args.max_target_size

        # Encoder-Decoder for Trace Generation
        source_tokens = js.code_tokens[: max_source_size - 6]
        source_tokens = ["<s>", "<encoder-decoder>", "</s>"] + source_tokens + ["</s>", "<mask0>", "</s>"]
        source_ids = self.tokenizer.convert_tokens_to_ids(source_tokens)
        source_padding_length = max_source_size - len(source_ids)
        source_ids += [self.tokenizer.pad_token_id for _ in range(source_padding_length)]

        target_tokens = self.tokenizer.tokenize("None") # generate
        target_tokens = ["<mask0>"] + target_tokens + [self.tokenizer.sep_token]     
        
        target_ids = self.tokenizer.convert_tokens_to_ids(target_tokens)
        padding_length = self.args.max_target_size - len(target_ids)
        target_ids += [self.tokenizer.pad_token_id] * padding_length

        return (
            torch.tensor(source_ids),
            torch.tensor(target_ids)
        )