import ast


class GlobalVariableExtraction(ast.NodeVisitor):
    """ 
        We extract all the left hand side of the global (top-level) assignments
    """

    def __init__(self) -> None:
        super().__init__()
        self.results = dict()

    def visit_Assign(self, node):
        if len(node.targets) != 1:
            raise ValueError("Only unary assignments are supported")
        node_value = node.value.__dict__
        if node.targets[0].id not in self.results.keys():
            if 'value' in node_value.keys():
                self.results[node.targets[0].id] = node_value['value']
                node.value.__dict__['name'] = node.targets[0].id  # store variable name in dict
            else:
                self.results[node.targets[0].id] = None
        # print(self.results)

    def visit_FunctionDef(self, node):
        # function definitions are not global, so they cannot be visited by default 
        pass
