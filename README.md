# Artifact for "Planning a Large Language Model for Static Detection of Runtime Errors in Code Snippets"

``ORCA`` is a novel approach that guides a Large Language Model (LLM) to autonomously plan and navigate control flow graphs (CFGs) for predictive execution of (in)complete code snippets, enabling static detection of runtime errors efficiently and cost-effectively. 

## Purpose
This artifact has been archived on a public archival repository ([Zenodo](https://zenodo.org/records/14910225)), qualifying it for the **Available** badge. Moreover, it contains well-documented source code for replicating all experiments, along with all data and LLM outputs, in line with the expectations for the **Functional** and **Reusable** badges.

## Provenance
The source code, data, and model outputs are publicly available on ([GitHub](https://github.com/SmitPatel910/orca)) and ([Zenodo](https://zenodo.org/records/14910225))

## Getting Started
This section describes the prerequisites and contains instructions, to get the project up and running.

### Setup 

#### Hardware Requirements
``Baseline B0``: The baseline CodeExecutor transformer model requires a __GPU machine__ for execution.

``ORCA`` requires access to OpenAI API credentials to use __gpt-3.5-turbo__. However, we also provide all LLM responses for the dataset (see `output`), and this can be skipped for experiments' replication.

#### Project Environment
Currently, ``ORCA`` works well on Ubuntu OS, and can be set up easily with all the prerequisite packages by following these instructions (if ``conda`` is already installed, update to the latest version with ``conda update conda``, and skip steps 1-3):
  1. Download the latest, appropriate version of [conda](https://repo.anaconda.com/miniconda/) for your machine (tested with ``conda 24.1.2``).
  2. Install  it by running the `conda_install.sh` file, with the command:
     ```bash
     $ bash conda_install.sh
     ```
  3. Add `conda` to bash profile:
     ```bash
     $ source ~/.bashrc
     ```
  4. Navigate to ``ORCA`` (top-level directory) and create a conda virtual environment with the included `environment.yml` file using the following command:     
     ```bash
     $ conda env create -f environment.yml
     ```

     To test successful installation, make sure ``orca`` appears in the list of conda environments returned with ``conda env list``.
  5. Activate the virtual environment with the following command:     
     ```bash
     $ conda activate orca
     ```
  
#### API Key Setup
__ORCA__ traverse the Control flow graph with the Observation, Reasoning, and Actions, while carefully tracking the Symbol Table after each block. Since this process requires a  ``higher token limit``, we’ve chosen to use the ``gpt-3.5-turbo (gpt-35-turbo-0613)`` model with the ``2023-05-15`` API version to ensure the successful graph traversal.
To get started, simply set up the model and fill in your credentials to use the ``ORCA`` model in the `.env` file.
```bash
   AZURE_OPENAI_ENDPOINT = ""
   AZURE_OPENAI_KEY = ""
   AZURE_API_VERSION = ""
   ```
---
### Directory Structure
1. __dataset__ - Contains the dataset files.
    - **baseline** - Contains the dataset files for baseline - ``CodeExecutor (B0)``.
    - **fixeval_cfg_b0.json** and **fixeval_incom_cfg_b0.json** - dataset files for ``ORCA`` and ``Other Baselines (B1 and B2)``
1. __dataset_builder__ - Includes all the modules required to __rebuild__ the dataset.
    - **Input_Variable_location** - Filter out the main dataset based on the input variable lines location.
    - **Hunter** - Collect the ground truth data by running the instances.
    - **CFG** - Build the Control Flow Graph for the instances.
    - **Sampling** - Randomly select the submissions (Buggy & Non-buggy) from all possible problem ids and merge them.
    - **Incomplete_Script** - Randomly select the submissions (Buggy & Non-buggy) having builtin or external libraries and remove `import statements` from it.
    - **temp_dataset** - Caching dataset files from all the modules.

1. __output__ - Contains the output files for ``All Baselines (B0, B1, B2)`` and  ``ORCA``.

1. __src__ - Contains source files for ``All Baselines (B0, B1, B2)`` and  ``ORCA``.
    - **baselines** - b0, b1, b2
    - **orca**

---    

### Accuracy Evaluation
To evaluate the accuracy of all baselines and the ORCA model for the research questions (RQs), refer to the table below.

|           Approach          |   Table # & RQ # in Paper   |    Directory Location   |      Run Command(s)      |
|:-----------------------:|:---------------------------:|:-----------------------:|:------------------------:|
|     __ORCA__ Results    | Table - 1 to 9, RQ - 1 to 5  |     `orca/src/orca/`    | `python show_results.py` |
| Baseline __Bo__ Results | Table - 5,6,8, RQ - 3 & 4  | `orca/src/baselines/b0` | `python show_results.py` |
| Baseline __B1__ Results | Table - 1 to 6, RQ - 1 to 3 | `orca/src/baselines/b1` | `python show_results.py` |
| Baseline __B2__ Results | Table - 1 to 6, RQ - 1 to 3 | `orca/src/baselines/b2` | `python show_results.py` |

---

### Steps to Reproduce Results
Follow the steps below to replicate the results for ``baselines`` and the ``ORCA`` model. 

#### For Baseline **B0**
1. Navigate to the `orca/src/baselines/b0` directory.
2. Run the following commands:
    ```bash
    python run.py
    python show_results.py
    ```
#### For Baseline **B1** and **B2**

1. Navigate to the respective directories:
   - **B1**: `orca/src/baselines/b1/`
   - **B2**: `orca/src/baselines/b2/`

2. Run the Pipeline:  
   Use the following command to execute the pipeline. You can either replace the parameters with custom values or stick to the default settings:  
   - **Default Parameters**:  
     - `temperature`: `0.7`  
     - `seed`: `42`  
     - `timeout`: `120`  
   ```bash
   python pipeline.py --model <LLM_MODEL> --temperature <FLOAT> --seed <INT> --timeout <INT>
   ```
3. View the Results:
   After running the pipeline, check the results using the following command:
    ```bash
    python show_results.py
    ```
#### For **ORCA**
1. Navigate to the `orca/src/orca/` directory.
2. Run the Pipeline:  
Use the following command to execute the pipeline. You can either replace the parameters with custom values or stick to the default settings:  
   - **Default Parameters**:    
     - `temperature`: `0.7`  
     - `seed`: `42`  
     - `timeout`: `120`
    ```bash
    python pipeline.py --model <LLM_MODEL> --temperature <FLOAT> --seed <INT> --timeout <INT>
    ```
3. View the Results:
   After running the pipeline, check the results using the following command:
    ```bash
    python show_results.py
    ```

---

### Inference: Run ORCA for Custom Dataset
1. Navigate to the `orca/src/orca/inference` directory.
2. Run the Pipeline:  
Use the following command to execute the pipeline. You can either replace the parameters with custom values or stick to the default settings:  
   - **Default Parameters**:    
     - `temperature`: `0.7`  
     - `seed`: `42`  
     - `timeout`: `120`
     - `input_dir`: `../../../dataset/dataset.json`
     - `output_dir`: `../../../output/orca`
    ```bash
    python pipeline.py --model <LLM_MODEL> --temperature <FLOAT> --seed <INT> --timeout <INT> --input_dir <Dataset Directory Path> --output_dir <Output Directory Path>
    ```
3. **CFG Tool Limitation**:
The CFG (Control Flow Graph) tool work with only one method because it can not map block connection for the method calls. Ensure that each datapoint in your dataset contains one method.

### Reproducing the Dataset

1. Download the [FixEval](https://drive.google.com/file/d/1Za85w9lwyaaoVRRIuW5mWpAjnuETfLxt/view?usp=sharing) Dataset and and move it to the ```orca/dataset``` directory.
2. Download the [Testcases](https://drive.google.com/file/d/1NTJf-AnHEXRZJGgVz4o2_vI-VLGm23eg/view?usp=sharing) zip file and Extract it to the `orca/dataset_builder/Hunter/` directory.
3. Go to ```orca/dataset_builder``` directory and run ```python -W ignore script.py``` to build the dataset.
4. Go to ```orca/src/baselines/b0/dataset_building``` directory and run ```python -W ignore script.py``` to build the dataset for Code Executor Baseline (B0).

---

## Contributing Guidelines
- Code should carry appropriate comments, wherever necessary, and follow the docstring convention in the repository.

- If you see something that could be improved, send a pull request! We are always happy to look at improvements, to ensure that `orca`, as a project, is the best version of itself.
If you think something should be done differently (or is just-plain-broken), please create an issue.

--- 

## License
See the [LICENSE](LICENSE) file for more details.
