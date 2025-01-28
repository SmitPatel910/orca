import time
from absl import app
from tqdm import tqdm
from python_graphs import control_flow
from python_graphs import control_flow_graphviz
from python_graphs import control_flow_test_components as tc
from python_graphs import program_utils

from utils import replace_code_in_file, reset_file_content
from utils import get_block_ranges_and_statements, get_block_connections, renumber_cfg_blocks, generate_cfg_text

def get_cfg_from_function(testFun):
    return control_flow.get_control_flow_graph(testFun)

def generate_cfg_for_code(code, mode):
    try:
        reset_file_content('example.py')
        replace_code_in_file('example.py', code)
        from example import testFun
        
        cfg = get_cfg_from_function(testFun)

        if mode == 'single':
            source = program_utils.getsource(testFun)
            control_flow_graphviz.render(cfg, include_src=source, path='cfg.png')
            time.sleep(2) # Wait for the image to be generated

        cfg_block_range, cfg_block_statements = get_block_ranges_and_statements(cfg, code)
        if cfg_block_range == None or cfg_block_statements == None: return None

        cfg_block_connection = get_block_connections(cfg_block_range, cfg)
        if cfg_block_connection == None: return None

        cfg_block_statements, cfg_block_range, cfg_block_connection = renumber_cfg_blocks(cfg_block_statements, cfg_block_range, cfg_block_connection)
        if cfg_block_statements == None or cfg_block_range == None or cfg_block_connection == None: return None

        cfg_text = generate_cfg_text(cfg_block_statements, cfg_block_connection, cfg_block_range)
        if cfg_text == "":
            return None
        
        return cfg_block_statements, cfg_block_range, cfg_block_connection, cfg_text
    
    except Exception as e:
        print("Error in CFG Generation: ", e)
        return None
