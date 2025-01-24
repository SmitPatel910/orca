SYSTEM = '''
Task: Execute the provided code and identify any runtime exceptions that occur.

Guidelines for Execution:
- Run the code as provided.
- Record any runtime exceptions that occur during execution.
- Stop the execution immediately when a runtime exception is encountered.
- Ensure the execution sequence proceeds from line 1 to the last line of the code snippet, or until an error is encountered.

Expected Output Format:
- Indicate whether a runtime exception occurred (Yes / No).
- If an error is detected, specify the type of the error.
- Provide a list of the lines executed up to the line where the error occurred or the last line of the code snippet.
- Include the error message if an error is detected.

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