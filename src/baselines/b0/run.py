from __future__ import absolute_import, division, print_function
import json
import torch
import random
import logging
import argparse
import numpy as np
from tqdm import tqdm
from pathlib import Path
from model import Seq2Seq
from dataset import CodeCoverageDataset
from torch.nn.parallel import DataParallel
from torch.utils.data import DataLoader, SequentialSampler
from transformers import (AdamW, get_linear_schedule_with_warmup, RobertaConfig, RobertaModel, RobertaTokenizer)

logger = logging.getLogger(__name__)        

def set_seed(args):
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if args.n_gpu > 0:
        torch.cuda.manual_seed_all(args.seed)

def evaluate(args, eval_dataset, model, tokenizer):
    eval_dataloader = DataLoader(eval_dataset, sampler=SequentialSampler(eval_dataset), 
                                 batch_size=args.eval_batch_size, drop_last=False)
    # Evaluate!
    logger.warning("***** Running evaluation *****")
    logger.warning(f"  Num examples = {len(eval_dataset)}")
    logger.warning(f"  Batch size = {args.eval_batch_size}")

    model = DataParallel(model)

    model.eval() 
    pred_list = []
    gold_list = []
    for batch in tqdm(eval_dataloader):
        source_ids, target_ids =[x.to(args.device) for x in batch]                
        with torch.no_grad():
            preds = model(source_ids)   
            # convert ids to text
            for i,pred in enumerate(preds):
                t = pred[0].cpu().numpy()
                t = list(t)
                if 0 in t:
                    t = t[:t.index(0)]
                text = tokenizer.decode(t,clean_up_tokenization_spaces=False)
                pred_list.append(text)
    return pred_list

def load_dataset(dataset_path):
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)
    return dataset

# Fetch the Symbol Table
def fetch_the_symbol_table(data):
    extracted_line_numbers = []
    prob_sub_dict = []
    for segment in data:
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
    
    return prob_sub_dict, extracted_line_numbers

# Parse the CodeExecutor Prediction
def parse_the_prediction(dataset, response):
    pred_exe_symbol_table = {}

    for id, prob_sub in enumerate(dataset.keys()):
        # Get the prediction for the current Index
        code_executor_pred = response[int(id)]

        prob_sub_dict = []
        extracted_line_numbers = []

        line_segments = code_executor_pred.split("<line>")
        
        prob_sub_dict, extracted_line_numbers = fetch_the_symbol_table(line_segments)
        if not prob_sub in pred_exe_symbol_table:   pred_exe_symbol_table[prob_sub] = {}
        pred_exe_symbol_table[prob_sub]["symbol_table"] = prob_sub_dict
        pred_exe_symbol_table[prob_sub]["execution_order"] = extracted_line_numbers

    return pred_exe_symbol_table

def main():
    parser = argparse.ArgumentParser()

    ## Other parameters
    parser.add_argument("--config_name", default=None, type=str,
                        help="Optional pretrained config name or path if not the same as model_name_or_path")
    parser.add_argument("--max_source_size", default=512, type=int,
                        help="Optional input sequence length after tokenization.")
    parser.add_argument("--max_target_size", default=512, type=int,
                        help="Optional output sequence length after tokenization.")
    parser.add_argument("--per_gpu_train_batch_size", default=4, type=int,
                        help="Batch size per GPU/CPU for training.")
    parser.add_argument("--train_batch_size", default=8, type=int,
                        help="Batch size per GPU/CPU for evaluation.")
    parser.add_argument("--eval_batch_size", default=32, type=int,
                        help="Batch size per GPU/CPU for evaluation.")
    parser.add_argument("--num_train_epochs", default=5, type=int,
                        help="Total number of training epochs to perform.")
    parser.add_argument('--gradient_accumulation_steps', type=int, default=1,
                        help="Number of updates steps to accumulate before performing a backward/update pass.")
    parser.add_argument("--learning_rate", default=5e-5, type=float,
                        help="The initial learning rate for Adam.")
    parser.add_argument("--weight_decay", default=0.0, type=float,
                        help="Weight deay if we apply some.")
    parser.add_argument("--adam_epsilon", default=1e-8, type=float,
                        help="Epsilon for Adam optimizer.")
    parser.add_argument("--max_grad_norm", default=1.0, type=float,
                        help="Max gradient norm.")
    parser.add_argument('--seed', type=int, default=42,
                        help="random seed for initialization")
    parser.add_argument("--beam_size", default=1, type=int,
                        help="beam size for beam search") 

    args = parser.parse_args()

    # Setup CUDA, GPU.
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    args.n_gpu = torch.cuda.device_count()
    args.device = device

    # Setup logging
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S',
                        level=logging.INFO)
    
    # Setting up the paths for the dataset and the temporary dataset directory.
    script_directory = Path(__file__).resolve()
    base_directory = script_directory.parents[3]

    output_dir = base_directory / 'output' / 'baseline' / 'b0'
    args.output_dir = output_dir
    args.log_file = Path(args.output_dir) / 'log.txt'
    if not Path(args.output_dir).exists():
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    if Path(args.log_file).is_file():
        logfile = logging.FileHandler(args.log_file, 'a')
    else:
        logfile = logging.FileHandler(args.log_file, 'w')
    fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%m/%d/%Y %H:%M:%S %p')
    logfile.setFormatter(fmt)
    logger.addHandler(logfile)
    logger.warning(f"Device: {device}, n_gpu: {args.n_gpu}")

    # Set seed
    set_seed(args)

    tokenizer = RobertaTokenizer.from_pretrained('microsoft/codeexecutor')
    special_tokens_list = ['<line>', '<state>', '</state>', '<dictsep>', '<output>', '<indent>',
                            '<dedent>', '<mask0>']
    for i in range(200):
        special_tokens_list.append(f"<{i}>")
    special_tokens_dict = {'additional_special_tokens': special_tokens_list}
    tokenizer.add_special_tokens(special_tokens_dict)
    config = RobertaConfig.from_pretrained('microsoft/codeexecutor')

    config.is_decoder = True
    encoder = RobertaModel.from_pretrained('microsoft/codeexecutor', config=config)
    encoder.resize_token_embeddings(len(tokenizer))
    decoder = encoder

    model = Seq2Seq(encoder=encoder, decoder=decoder, config=config, beam_size=args.beam_size,
                    max_length=args.max_target_size, sos_id=tokenizer.convert_tokens_to_ids(["<mask0>"])[0],
                    eos_id=tokenizer.sep_token_id)
    model.to(args.device)

    logger.warning(f"Training/evaluation parameters {args}")

    dataset_path = base_directory / 'dataset' / 'baseline'
    complete_dataset_path = dataset_path / 'fixeval_cfg_b0.json'
    incomplete_dataset_path = dataset_path / 'fixeval_incom_cfg_b0.json'

    logger.info(f"Loading Complete Code dataset from {complete_dataset_path}")
    eval_complete_dataset = CodeCoverageDataset(tokenizer, complete_dataset_path, args, logger)
    
    logger.info(f"\nLoading Incomplete Code dataset from {incomplete_dataset_path}")
    eval_incomplete_dataset = CodeCoverageDataset(tokenizer, incomplete_dataset_path, args, logger)

    logger.info("\nEvaluating Complete Code dataset")
    eval_complete_results = evaluate(args, eval_complete_dataset, model, tokenizer)

    logger.info("\nEvaluating Incomplete Code dataset")
    eval_incomplete_results = evaluate(args, eval_incomplete_dataset, model, tokenizer)


    # Parse the Output:
    logger.info("\nParsing the output")
    complete_dataset = load_dataset(complete_dataset_path)
    incomplete_dataset = load_dataset(incomplete_dataset_path)
    
    # Get the parsed output for the Complete Code
    parsed_prediction = parse_the_prediction(complete_dataset, eval_complete_results)
    # Get the parsed output for the Incomplete Code
    incom_parsed_prediction = parse_the_prediction(incomplete_dataset, eval_incomplete_results)

    output_dir = base_directory / 'output' / 'baseline' / 'b0'
    complete_code_output_dir = output_dir / 'codeExe_fixeval.json'
    incomplete_code_output_dir = output_dir / 'codeExe_incom_fixeval.json'

    logger.info(f"\nSaving results for Complete Code dataset at {complete_code_output_dir}")
    with open(complete_code_output_dir, 'w') as json_file:
        json.dump(parsed_prediction, json_file, default=str)
    
    logger.info(f"\nSaving results for Incomplete Code dataset at {incomplete_code_output_dir}")
    with open(incomplete_code_output_dir, 'w') as json_file:
        json.dump(incom_parsed_prediction, json_file, default=str)
    
    logger.info("\nResults saved successfully!")

if __name__ == "__main__":
    main()