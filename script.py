import os
import json
from pathlib import Path

from Input_variable_location.script import filter_original_dataset

from Hunter.script import get_execution_trace
from Hunter.trace_operation import extract_trace_info
from Hunter.input_value_injection import inject_input_values

from CFG.cfg_fixeval import generate_cfg

from Sampling.sampling_dataset import main

from Incomplete_Script.incomplete_dataset_script import make_incomplete_dataset

# Setting up the paths for the dataset and the temporary dataset directory.
script_directory = Path(__file__).resolve()
base_directory = script_directory.parents[1]

def A_filter_dataset(load_dataset_path, save_dataset_path):
      '''
            Submissions are omitted based on the following criteria to ensure compatibility with CFG tools:

            1. Control Structures:
            - Submissions containing input within control structures like for loops, while loops, 
            or during method definitions/calls are omitted.

            2. Compact Conditional Statements:
            - Submissions with if-else statements on the same line are omitted because CFG tools 
            often generate incorrect control flow graphs for such patterns.

            3. Method Definitions:
            - Submissions contianing more than one method definition are omitted as CFG tool can not make connections between method calls and returns. 
            ---> Although, this is not the ORCA limitation, but the limitation of the CFG tool.
            ---> By establishing the method call and return connections manually, this limitation can be overcome and ORCA can be used to generate the CFG for such submissions.

            4. Syntax and Compatibility Issues:
            - Submissions with syntax errors which prevent AST parsing are omitted.
            - Submissions written in Python 2 are omitted due to potential incompatibilities with tools expecting Python 3 syntax.
            - Submissions exhibiting scoping issues are also omitted as they may lead to incorrect CFG constructions.
      '''

      print("Filtering the dataset based on the defined criteria...")
      path = base_directory / 'dataset_builder' / 'Input_variable_location'
      filtered_dataset = filter_original_dataset(path, load_dataset_path)
      print("Dataset filtered successfully!\n")

      with open(save_dataset_path, 'w') as file:
          json.dump(filtered_dataset, file, indent=4)
      
      return filtered_dataset

def B_get_ground_truth(filtered_dataset, save_buggy_dataset, save_non_buggy_dataset):
      '''
            Use Hunter tool to run each submission with the test case for each submission and get the execution trace.
      '''

      print("Running Hunter Tool to get the execution trace for each submission...")
      path = base_directory / 'dataset_builder' / 'Hunter'
      
      get_execution_trace(path, filtered_dataset)
      print("Execution trace obtained successfully!")
      print()

      print("Extracting trace information...")
      buggy_dataset, non_buggy_dataset = extract_trace_info(path)
      print("Trace information extracted successfully!\n")

      with open(save_buggy_dataset, 'w') as file:
            json.dump(buggy_dataset, file, indent=4)
      with open(save_non_buggy_dataset, 'w') as file:
            json.dump(non_buggy_dataset, file, indent=4)

      return buggy_dataset, non_buggy_dataset

def C_inject_test_case_values(filtered_dataset, buggy_dataset, non_buggy_dataset, save_buggy_dataset_ready_for_cfg, save_non_buggy_dateset_ready_for_cfg):
      '''
            Inject the test case values into the code by removing the input() statements.
      '''
      print("Injecting Test Case Values into the code by removing the input() statements...")
      buggy_dataset_ready_for_cfg, non_buggy_dateset_ready_for_cfg = inject_input_values(filtered_dataset, buggy_dataset, non_buggy_dataset)
      print("Test Case Values injected successfully!\n")

      with open(save_buggy_dataset_ready_for_cfg, 'w') as file:
            json.dump(buggy_dataset_ready_for_cfg, file, indent=4)

      with open(save_non_buggy_dateset_ready_for_cfg, 'w') as file:
            json.dump(non_buggy_dateset_ready_for_cfg, file, indent=4)      

      return buggy_dataset_ready_for_cfg, non_buggy_dateset_ready_for_cfg

def D_generate_cfg(buggy_dataset_ready_for_cfg, non_buggy_dateset_ready_for_cfg, save_buggy_cfg_dataset, save_non_buggy_cfg_dataset):
      '''
            Get the CFG for the dataset instances.
      '''
      
      print("Generating CFG for the dataset instances...")
      buggy_dataset, non_buggy_dataset = generate_cfg(buggy_dataset_ready_for_cfg, non_buggy_dateset_ready_for_cfg)
      print("CFG generated successfully!\n")

      with open(save_buggy_cfg_dataset, 'w') as file:
            json.dump(buggy_dataset, file, indent=4)
      with open(save_non_buggy_cfg_dataset, 'w') as file:
            json.dump(non_buggy_dataset, file, indent=4)

      return buggy_dataset, non_buggy_dataset

def E_sample_and_merge_dataset(buggy_dataset, non_buggy_dataset, save_merged_dataset):
      '''
            Sample the dataset instances for training and testing.
      '''
      print("Sampling the dataset instances for testing")
      merged_dataset = main(buggy_dataset, non_buggy_dataset)
      print("Dataset Sampled and Merged successfully!\n")
      
      with open(save_merged_dataset, 'w') as file:
            json.dump(merged_dataset, file, indent=4)

      return merged_dataset

def F_make_incomplete_dataset(buggy_dataset, non_buggy_dataset, save_incomplete_dataset):
      '''
            Make Incomplete Dataset by removing 'import' statements from the code.
      '''
      print("Making Incomplete Dataset by removing 'import' statements from the code...")
      incomplete_dataset = make_incomplete_dataset(buggy_dataset, non_buggy_dataset)
      print("Incomplete Dataset created successfully!\n")

      with open(save_incomplete_dataset, 'w') as file:
            json.dump(incomplete_dataset, file, indent=4)

      return incomplete_dataset

if __name__ == '__main__':

      temp_dataset_dir_path = base_directory / 'dataset_builder' / 'temp_dataset'


      # A ---> Filter the dataset based on the defined criteria.
      base_dataset_path = base_directory / 'dataset' / 'fixeval_original.json'
      save_dataset_path = temp_dataset_dir_path / 'filtered_dataset.json'
      if os.path.exists(save_dataset_path):
            print("Filtered dataset already exists, loading the dataset...\n")
            with open(save_dataset_path, 'r') as file:
                  filtered_dataset = json.load(file)
      else:
            filtered_dataset = A_filter_dataset(base_dataset_path, save_dataset_path)
      
      # B ---> Get the Ground Truth for the filtered dataset by actually running the submissions.
      save_buggy_dataset = temp_dataset_dir_path / 'buggy_trace_dataset.json'
      save_non_buggy_dataset = temp_dataset_dir_path / 'non_buggy_trace_dataset.json'
      if os.path.exists(save_buggy_dataset) and os.path.exists(save_non_buggy_dataset):
            print("Ground Truth already exists, loading the dataset...\n")
            with open(save_buggy_dataset, 'r') as file:
                  buggy_dataset = json.load(file)
            with open(save_non_buggy_dataset, 'r') as file:
                  non_buggy_dataset = json.load(file)
      else:
            buggy_dataset, non_buggy_dataset = B_get_ground_truth(filtered_dataset, save_buggy_dataset, save_non_buggy_dataset)
      

      # C ---> Inject the test case values into the code by removing the input() statements.
      save_buggy_dataset_ready_for_cfg = temp_dataset_dir_path / 'buggy_dataset_ready_for_cfg.json'
      save_non_buggy_dateset_ready_for_cfg = temp_dataset_dir_path / 'non_buggy_dateset_ready_for_cfg.json'
      if os.path.exists(save_buggy_dataset_ready_for_cfg) and os.path.exists(save_non_buggy_dateset_ready_for_cfg):
            print("Test Case Values already injected, loading the dataset...\n")
            with open(save_buggy_dataset_ready_for_cfg, 'r') as file:
                  buggy_dataset_ready_for_cfg = json.load(file)
            with open(save_non_buggy_dateset_ready_for_cfg, 'r') as file:
                  non_buggy_dateset_ready_for_cfg = json.load(file)
      else:
            buggy_dataset_ready_for_cfg, non_buggy_dateset_ready_for_cfg = C_inject_test_case_values(filtered_dataset, buggy_dataset, non_buggy_dataset, save_buggy_dataset_ready_for_cfg, save_non_buggy_dateset_ready_for_cfg)

      # D ---> Get the CFG for the dataset instances.
      save_buggy_cfg_dataset = temp_dataset_dir_path / 'buggy_cfg_dataset.json'
      save_non_buggy_cfg_dataset = temp_dataset_dir_path / 'non_buggy_cfg_dataset.json'
      if os.path.exists(save_buggy_cfg_dataset) and os.path.exists(save_non_buggy_cfg_dataset):
            print("CFG already exists, loading the dataset...\n")
            with open(save_buggy_cfg_dataset, 'r') as file:
                  buggy_cfg_dataset = json.load(file)
            with open(save_non_buggy_cfg_dataset, 'r') as file:
                  non_buggy_cfg_dataset = json.load(file)
      else:
            buggy_cfg_dataset, non_buggy_cfg_dataset = D_generate_cfg(buggy_dataset_ready_for_cfg, non_buggy_dateset_ready_for_cfg, save_buggy_cfg_dataset, save_non_buggy_cfg_dataset)

      
      # E ---> Sample the dataset instances and merge them.
      save_merged_dataset = temp_dataset_dir_path / 'fixeval_merged_cfg.json'
      save_merged_dataset_2 = base_directory / 'dataset' / 'fixeval_merged_cfg.json'
      if os.path.exists(save_merged_dataset):
            print("Merged Dataset already exists, loading the dataset...\n")
            with open(save_merged_dataset, 'r') as file:
                  merged_dataset = json.load(file)
      else:
            merged_dataset = E_sample_and_merge_dataset(buggy_cfg_dataset, non_buggy_cfg_dataset, save_merged_dataset)
            with open(save_merged_dataset_2, 'w') as file:
                  json.dump(merged_dataset, file, indent=4)

      # F ---> Make Incomplete Dataset by removing 'import' statements from the code.
      save_incomplete_dataset = temp_dataset_dir_path / 'fixeval_incom_merged_cfg.json'
      save_incomplete_dataset_2 = base_directory / 'dataset' / 'fixeval_incom_merged_cfg.json'
      if os.path.exists(save_incomplete_dataset):
            print("Incomplete Dataset already exists, loading the dataset...\n")
            with open(save_incomplete_dataset, 'r') as file:
                  incomplete_dataset = json.load(file)
      else:
            incomplete_dataset = F_make_incomplete_dataset(buggy_cfg_dataset, non_buggy_cfg_dataset, save_incomplete_dataset)
            with open(save_incomplete_dataset_2, 'w') as file:
                  json.dump(incomplete_dataset, file, indent=4)
      
      print("Dataset Builder Script Completed Successfully!")