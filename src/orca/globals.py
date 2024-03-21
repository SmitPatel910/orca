SYSTEM = '''
Task: Detect errors(runtime, typeerror) by traversing the Control Flow Graph (CFG) of a Python program. Each block in the CFG represents a segment of code, with conditions guiding the flow from one block to another based on condition evaluation. The symbol table should be used to track variable states & types and execute code within each block. The objective is to catch type mismatches and other common runtime errors efficiently during traversal.

Input Details: Each block in the CFG is described as follows:
Block number: A unique identifier for the block.
Statement: The Python code executed in this block.
(When a block includes the 'iterator' keyword, you must update the iterator variable's value based on its associated range or iterable list. Additionally, update the variable's type in the symbol table to reflect the current value type.)
Next, if True: The identifier of the next block executed if the condition evaluates to True.
Next, if False: The identifier of the next block executed if the condition evaluates to False.

Error Detection:
Precisely identify and document the errors (RuntimeError, TypeError), during code execution or condition evaluation. This includes common runtime issues like division by zero, accessing undefined variables, and specifically, type errors resulting from operations on incompatible data types.

Traversal Process:
- Begin the traversal at the first block of the CFG, and document the symbol table with the initial variable states and types.
- Each block will have 2 types of statements: statement execution and condition evaluation.

- For Statement Execution:
Observation: Carefully review the current block's statement and the symbol table, paying particular attention to the data types and values of variables involved.
Reasoning: Before executing any code, evaluate the statement for type compatibility and logical coherence, using the identified variables' types and values.
Action: If an error (RunTime, TypeError) is anticipated or detected, immediately document the specific error type and the block number where it was identified. Stop the traversal process by adding <STOP> to the output.

- For Condition Evaluation:
The last line in each block is crucial as it contains a condition determining the next block in the sequence. To evaluate the condition, follow these steps:
Observation: Review the condition and gether the all the variables names, their values, and types from the symbol table.
Reasoning: Put all the variables' values and types within the condition to evaluate the condition. Check for any type errors and logical coherence.
Action: Determine the condition's truth value (True or False) and proceed accordingly. Move to the next block as per the True or False path.
- Before moving to the next block, update the symbol table with the new variable states and types after executing the current block's code and document it.

Continue this traversal process until the traversal reaches the end block of the CFG (<END>) or anticipating an error (runtime, type) during reasoning.

End Goal: Traverse the CFG, by evaluating the conditions and executing the code in each block, Once the error is detected, record the error type and the block in which it occurred and <STOP> the traversal process.

Submit the following details for each block:
"""
Block: <block_id>
{Block Content}
Observation:
Reasoning:
Action:
Symbol Table: {'x': (2, int), 'y': (3.5, float), ...}

- Error Information:
Error Type: <type>
Block: <block_id>
Observation:
Reasoning:
Action:
"""
'''

USER = '''
Control Flow Graph (CFG):
"""
<CODE>
"""

Traverse the provided CFG to catch the errors (Runtime, TypeError) and document the symbol table at each block.
'''