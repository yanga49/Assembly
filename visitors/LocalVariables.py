
import ast

class LocalVariableExtraction(ast.NodeVisitor):
    """ 
        We extract all the left hand side of the local assignments
    """
    
    def __init__(self) -> None:
        super().__init__()
        self.results = set()

    def visit_Assign(self, node):
        if len(node.targets) != 1:
            raise ValueError("Only unary assignments are supported")
        self.results.add(node.targets[0].id)
    

    def visit_FunctionDef(self, node):
        for contents in node.body:
            self.visit(contents)
        if node.args.args:
            for i in range(len(node.args.args)):
                self.results.add(node.args.args[i].arg)
