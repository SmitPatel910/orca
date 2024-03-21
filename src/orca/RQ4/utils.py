import ast

def extract_scopes_with_line_numbers(code):
    tree = ast.parse(code)
    categorized_scopes = {
        'for': [],
        'while': [],
        'if': [],
        'simple_statement': []
    }

    class ScopeExtractor(ast.NodeVisitor):
        def extract_scope(self, node, scope_type):
            start_line = node.lineno
            end_line = node.end_lineno
            scope_code = ast.get_source_segment(code, node)
            categorized_scopes[scope_type].append((start_line, end_line, scope_code))

        def visit_For(self, node):
            self.extract_scope(node, 'for')

        def visit_While(self, node):
            self.extract_scope(node, 'while')

        def visit_If(self, node):
            self.extract_scope(node, 'if')

        def generic_visit(self, node):
            if isinstance(node, ast.Expr) or isinstance(node, ast.Assign) or isinstance(node, ast.AugAssign):
                start_line = node.lineno
                end_line = node.end_lineno
                stmt_code = ast.get_source_segment(code, node)
                categorized_scopes['simple_statement'].append((start_line, end_line, stmt_code))
            super().generic_visit(node)

    ScopeExtractor().visit(tree)
    return categorized_scopes

def get_scope(code):
    for_loop = []
    while_loop = []
    if_statement = []
    simple_statements = []

    categorized_scopes = extract_scopes_with_line_numbers(code)
    for scope_type, scopes in categorized_scopes.items():
        for start_line, end_line, scope in scopes:
            if scope_type == 'for':
                for_loop.append([start_line, end_line])
            elif scope_type == 'while':
                while_loop.append([start_line, end_line])
            elif scope_type == 'if':
                if_statement.append([start_line, end_line])
            else:
                simple_statements.append([start_line, end_line])
        
    return for_loop, while_loop, if_statement, simple_statements
