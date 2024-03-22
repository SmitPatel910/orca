# Static Detection of Runtime Errors in Partial Code Snippets via Planning for Large Language Model

Several studies have found numerous insecure code snippets in StackOverflow posts, with many making their way into popular open-source projects. Early detection of runtime errors and defects in these snippets is crucial to prevent costly fixes later in the development cycle. Researchers have developed various approaches, including static analysis, dynamic analysis, and machine learning, to address this need. However, they are either inaccurate due to overestimation or require dynamic instrumentation for the complete code execution.

In this paper, we propose ORCA, a novel ML-based approach that detects runtime errors in (in)complete code snippets without execution. In ORCA, we develop a novel planning technique that instructs a Large Language Model (LLM) to autonomously formulate a plan for predictive execution of code snippets, navigating through a control flow graph (CFG) to identify runtime errors. In executing the plan with the traversal of the CFG, the LLM identifies and reports any encountered runtime errors or exceptions. In our novel planning technique, we guide the LLM to pause at the branching point, focusing on the state of the symbol tables for variables’ values, thus minimizing error propagation in the LLM’s computation. We also instruct the LLM not to stop at each step in its execution plan, resulting the use of only one API call to the LLM. Our empirical evaluation on real-world code has shown that ORCA is effective and improves over the state-of-the-art techniques in runtime error detection as well as in predicting the execution traces in a program.

## Quick Start

1. Clone the repository or download the source code.
   ```bash
   https://github.com/sedoubleblinder/orca.git
2. Navigate to the ```src``` directory which contains the orca, baseline source code.
   ```bash
   cd src/orca
3. Create a ```.env ``` file inside the ```src/orca``` directory:
   ```bash
   AZURE_OPENAI_ENDPOINT = 
   AZURE_OPENAI_KEY = 
   AZURE_API_VERSION = 
   AZURE_OPENAI_DEPLOYMENT_NAME =
4. To run the ORCA tool, run the following command:
   ```bash
   python pipeline.py
5. To review accuracy metrics for ```RQ1-RQ4```, execute:
   ```bash
   python show_results.py
   ```
   
## Dataset Rebuilding Instructions

1. Set up the environment:
   ```bash
   conda env create -f environment.yml
   conda activate orca
2. Download the [FixEval](https://drive.google.com/file/d/1LqQVAXltAQdodzhoylgYvL0vt3r_u_Bu/view?usp=sharing) Dataset and and move it to the ```dataset``` directory.
3. In ```dataset_builder```, run ```python script.py``` to preprocess the dataset.
4. To generate execution traces, use the following commands in ```dataset_builder/Trace``` directory:
   ```bash
   python script.py
   python trace_operation.py
   python input_value_injection.py
6. For Control Flow Graph construction execute  ```python cfg_fixeval.py``` from ```dataset_builder/CFG```.
7. Sample the dataset by running ```python dataset_sample.py``` in ```dataset_builder/Sampling```
8. With the dataset prepared, initiate ORCA's pipeline with ```python pipeline.py``` in ```src/orca```.
   
   
