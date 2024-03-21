SYSTEM = '''
Task: Execute the given code and identify the runtime exceptions if any. 

The symbol table should be used to track variable states & types while executing the code on each line.

Continue this execution process until the execution reaches the end of the code or anticipating an error in the execution.

Provide the following information:
Error: Yes / No
Error Type: <type>
Execution including the errorline: [1, 2, ..., n]
Symbol Table: {'x': (2, int), 'y': (3.5, float), ...}
'''

USER = '''
Code:
"""
<CODE>
"""

Provide your output in the above format.
'''