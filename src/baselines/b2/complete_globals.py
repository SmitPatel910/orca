SYSTEM = '''
Task: Execute the provided code and identify any runtime exceptions.

Utilize the symbol table to actively track and update the states and types of variables as you execute each line of code. This dynamic tracking aids in a deeper understanding of variable interactions and contexts throughout the execution process.

Guidelines for Execution:
- Execute the code sequentially, starting from line 1 and proceed through each line until you encounter a runtime exception or reach the end of the code.
- Use the symbol table to handle and document changes in variable states and types at each step.
- Continue execution until runtime exception is encountered. Document this error along with the state of the symbol table at the time of the exception.

Output Requirements:
- Report whether an error occurred during execution (Yes/No).
- If an error occurred, specify the type of the error.
- Provide the list of executed lines leading up to and including the line where the error occurred.
- Include the exact error message encountered.
- Include the state of the symbol table at the point just before the error occurred. The symbol table should be formatted as: {'variable_name': (last_value, type), ...}.

Example Output:
Error: Yes / No
Error Type: <type>
Execution including the errorline: [1, 2, ..., n]
Error Message: <message>
Symbol Table: {'x': (2, int), 'y': (3.5, float), ...}
'''

USER = '''
Incomplete Code:
"""
<CODE>
"""

Please provide your output in the specified format.
'''