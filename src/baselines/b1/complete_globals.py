SYSTEM = '''
Task: Execute the provided code and identify any runtime exceptions.

Guidelines for Execution:
- Directly run the code as provided.
- Record any runtime exceptions that occur during the execution.
- Stop the execution at the first occurrence of any runtime exception.
- Ensure the execution sequence proceeds from line 1 to the last line of the code snippet or until an error is encountered.

Expected Output Format:
- Indicate whether any runtime exception occurred (Yes / No).
- If an error is detected, specify the type of the error.
- Provide a list of the lines executed up until and including the line where the error occurred.
- Include the exact error message encountered.

Example Output:
Error: Yes / No
Error Type: <type>
Execution including the errorline: [1, 2, ..., n]
Error Message: <message>
'''

USER = '''
Incomplete Code:
"""
<CODE>
"""

Provide your output in the specified format.
'''