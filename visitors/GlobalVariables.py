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
        if 'id' not in node.targets[0].__dict__.keys():  # skip array access nodes
            pass
        elif node.targets[0].id not in self.results.keys():
            if node.targets[0].id[-1] == '_' and 'right' in node_value.keys():  # check if array
                size = node_value['right'].__dict__
                self.results[node.targets[0].id] = size['value']  # store array name and size in dict
            elif 'value' in node_value.keys():  # check if constant or variable with value
                self.results[node.targets[0].id] = node_value['value']
                node.value.__dict__['name'] = node.targets[0].id  # store variable name and value in dict
            else:
                self.results[node.targets[0].id] = None
        # print(self.results)

    def visit_FunctionDef(self, node):
        # function definitions are not global, so they cannot be visited by default 
        pass
