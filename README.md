# Artifact for "Planning a Large Language Model for Static Detection of Runtime Errors in Code Snippets"

Large Language Models (LLMs) have been excellent in generating and reasoning about source code and the textual descriptions. They can recognize patterns, syntax, and semantics in code, making them effective in several software engineering tasks. However, they exhibit weaknesses in reasoning about the program execution. They primarily operate on static code representations, failing to capture the dynamic behavior and state changes that occur during program execution. In this paper, we advance the capabilities of LLMs in reasoning about program execution. We propose ORCA, a novel approach that instructs an LLM to autonomously formulate a plan to navigate through a control flow graph (CFG) for predictive execution of (in)complete code snippets. It acts as a predictive interpreter to “execute” the code. As a downstream task, we use __ORCA__ to statically identify any runtime errors for online code snippets. Early detection of runtime errors and defects in these snippets is crucial to prevent costly fixes later in the development cycle after they were adapted into a codebase. In our novel technique, __we guide the LLM to pause at the branching point, focusing on the state of the symbol tables for variables’ values, thus minimizing error propagation in the LLM’s computation.__ We also instruct the LLM not to stop at each step in its execution plan, resulting the use of only one prompt to the LLM, thus much cost-saving. Our empirical evaluation showed that ORCA is effective and improves over the state-of-the-art approaches in predicting the execution traces and in runtime error detection.

## Table of Contents
- [Getting Started](#getting-started)
  - [Setup](#setup)
    - [Project Environment](#project-environment)
    - [API Key Setup](#api-key-setup)
  - [Directory Structure](#directory-structure)
  - [Usage Guide](#usage-guide)
  - [License](#license)
  - [Contributing Guidelines](#contributing-guidelines)
    
## Getting Started
Welcome to the project! This section will guide you through getting everything set up and ready to go.

## Setup
To get started with this project, you'll need to set up your local environment and obtain necessary API keys.

### Project Environment
Currently, `ORCA` works well on Ubuntu OS, and can be set up easily with all the prerequisite packages by following these instructions (if conda is already installed, update to the latest version with conda update conda, and skip steps 1 - 3)
1. Download the latest, appropriate version of conda for your machine (tested with conda 24.1.2).
1. Install it by running the `conda_install.sh` file, with the command:
    ```bash 
        $ bash conda_install.sh
1. Add conda to bash profile:
    ```bash
        $ source ~/.bashrc
1. Navigate to `ORCA` (top-level directory) and create a conda virtual environment with the included environment.yml file using the following command:
    ```bash
        $ conda env create -f environment.yml
    ```
   To test successful installation, make sure `orca` appears in the list of conda environments returned with `conda env list`.

1. Activate the virtual environment with the following command:
    ```bash
    $ conda activate orca
    ```
### API Key Setup
__ORCA__ traverse the Control flow graph with the Observation, Reasoning, and Actions and keep track of Symbol Table after each block in only one prompt requires a higher token limit Large Language Model. Hence we used this model `gpt-35-turbo-16k` with the api version of `2023-05-15` to makesure successful traversal of the Control flow graph. Deploy the model and get the `Endpoint Key` to tun the `ORCA`.

## Directory Structure
1. __dataset__ - Contains the dataset files.
    - *baseline* - Contains the dataset filr for baseline - CodeExecutor (B0).
1. __dataset_builder__ - Contains all the module to build the dataset.
    - *Input_Variable_location* - Filter out the main dataset based on the input variable lines location.
    - *Huner* - Collect the ground truth data by running the instances.
    - *CFG* - Build the Control Flow Graph for the instances.
    - *Sampling* - Randomly select the submissions (Buggy & Non-buggy) from all possible problem ids and merge them.
    - *Incomplete_Script* - Randomly select the submissions (Buggy & Non-buggy) having builtin or external libraries and remove `import statements` from it.
    - *temp_dataset* - Caching dataset files from all the modules.
1. __output__ - Contains the output files for all the baselines and ORCA.
1. __src__ -
    - *baselines* - b0, b1, b2
    - *orca*
    
## Usage Guide

To get the accuracy of all the bsaelines and ORCA for RQs, follow the given table.

|           Task          |   Table # & RQ # in Paper   |    Directory Location   |      Run Command(s)      |
|:-----------------------:|:---------------------------:|:-----------------------:|:------------------------:|
|     __ORCA__ Results    | Table - 1 to 9, RQ - 1 to 5  |     `orca/src/orca/`    | `python show_results.py` |
| Baseline __Bo__ Results | Table - 5,6,8, RQ - 3 & 4  | `orca/src/baselines/b0` | `python show_results.py` |
| Baseline __B1__ Results | Table - 1 to 6, RQ - 1 to 3 | `orca/src/baselines/b1` | `python show_results.py` |
| Baseline __B2__ Results | Table - 1 to 6, RQ - 1 to 3 | `orca/src/baselines/b2` | `python show_results.py` |


### Reproduce the Results

- For baseline __B0__
  -  Go to `orca/src/baselines/b0` directory and run `python run.py` and `python show_results.py`

- Create a ```.env ``` file inside ```orca/src/orca/```, ```orca/src/baselines/b1/```, and ```orca/src/baselines/b2/``` directory.__
   ```bash
   AZURE_OPENAI_ENDPOINT = ""
   AZURE_OPENAI_KEY = ""
   AZURE_API_VERSION = ""
   ```
- For baseline __B1__ and __B2__
  -   Update the model name from the `model.py` file (line #54) in `orca/src/baselines/b1/`, `orca/src/baselines/b1/` for B1 and B2, respectively.
  -   Recommend to use Gpt 3.5 turbo model which matches with the ORCA tool to keep the same model among all approaches. Otherwise use GPT 3.5 base model.
  -   Run the pipeline for __B1__ and __B2__ by `python pipeline.py` from `orca/src/baselines/b1/`, `orca/src/baselines/b1/` directory, respectively.
  -   Check the results for __B1__ and __B2__ by `python show_results.py`.

- For __ORCA__
  -  Update the model name from the `model.py` file (line #52) in `orca/src/orca/`. Use GPT 3.5 Turbo model which offers higher token limit.
  -  Run the pipeline for __ORCA__ by `python pipeline.py` from `orca/src/orca/` directory.
  -  Check the results for __ORCA__ by `python show_results.py`.

### Reproduce the Dataset
1. Download the [FixEval](https://drive.google.com/file/d/1LqQVAXltAQdodzhoylgYvL0vt3r_u_Bu/view?usp=sharing) Dataset and and move it to the ```dataset``` directory.
2. Download the [Testcases](https://drive.google.com/file/d/1ZwyMC_p7JxKyIBtlS_frBpPau8PzXWi7/view?usp=sharing) zip file and Extract it to the `orca/dataset_builder/Hunter/` directory.
3. Go to ```orca/dataset_builder``` directory and run ```python -W ignore script.py``` to build the dataset.
4. Go to ```orca/src/baselines/b0/dataset_building``` directory and run ```python -W ignore script.py``` to build the dataset for Code Executor Baseline (B0).

## Contributing Guidelines
- Code should carry appropriate comments, wherever necessary, and follow the docstring convention in the repository.

If you see something that could be improved, send a pull request! We are always happy to look at improvements, to ensure that `orca`, as a project, is the best version of itself.
If you think something should be done differently (or is just-plain-broken), please create an issue.

## License
See the [LICENSE](LICENSE) file for more details.
