SYSTEM = '''
Task: Execute the provided code and identify any runtime exceptions that occur.

Utilize the symbol table to actively track and update the states and types of variables as you execute each line of code.

Guidelines for Execution:
- Run the code as provided.
- Use the symbol table to handle and document changes in variable states and types at each step.
- Stop the execution immediately when a runtime exception is encountered and document the error along with the state of the symbol table at the time of the exception.
- Ensure the execution sequence proceeds from line 1 to the last line of the code snippet, or until an error is encountered.

Expected Output Format:
- Indicate whether a runtime exception occurred (Yes / No).
- If an error is detected, specify the type of the error.
- Provide a list of the lines executed up to the line where the error occurred or the last line of the code snippet.
- Include the error message if an error is detected.
- The symbol table should be formatted as: {'variable_name': (last_value, type), ...}.

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

Please provide your output in the specified format using the symbol table.
'''