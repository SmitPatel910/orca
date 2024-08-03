import os
import sys
import hunter
from hunter import Q, VarsPrinter
from example import test_function

if __name__ == "__main__":
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
        # print(f"Error: {exc_type} - {exc_obj} - {exc_tb.tb_lineno} - {e}")

