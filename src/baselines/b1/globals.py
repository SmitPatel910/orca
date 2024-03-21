SYSTEM = '''
Task: Execute the given code and identify the runtime exceptions if any.

Continue this execution process until the execution reaches the end of the code or anticipating an error in the execution.

Provide the following information:
Error: Yes / No
Error Type: <type>
Execution including the errorline: [1, 2, ..., n]
Error Message: <message>
'''

USER = '''
Code:
"""
<CODE>
"""

Provide your output in the above format.
'''