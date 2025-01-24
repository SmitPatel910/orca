import os
import sys
import hunter
from hunter import Q, VarsPrinter
from example import test_function

if __name__ == "__main__":
    '''Main execution block to trace variables and execute a test function.

    This script uses the `hunter` library to trace variables and capture execution order. 
    It also handles exceptions raised during the execution of the `test_function`, capturing
    error details and type information.

    Environment Variables:
        - HUNTER_TRACE_VARS: A comma-separated list of variable names to trace.

    Execution Flow:
        1. Initializes variable tracing with `hunter`.
        2. Executes the `test_function`.
        3. Captures exceptions, if any, and extracts error details and type.
    '''
    variables_to_trace = os.getenv('HUNTER_TRACE_VARS', '').split(',')
    hunter.trace(Q(module='example', function='test_function', action=VarsPrinter(*variables_to_trace)))
    exexution_order = None
    error_detail = ""
    error_type = ""

    try:
        test_function()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        error_detail = exc_obj
        error_type = exc_type

