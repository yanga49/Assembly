
import ast

class LocalVariableExtraction(ast.NodeVisitor):
    """ 
        We extract all the left hand side of the local assignments
    """
    
    def __init__(self, global_vars) -> None:
        super().__init__()
        self.results = set()
        self.global_vars = global_vars

    def visit_Assign(self, node):
        if len(node.targets) != 1:
            raise ValueError("Only unary assignments are supported")
        # avoiding duplicates between global and local variables 
        if node.targets[0].id in self.global_vars:
            if len(node.targets[0].id) > 7:
                self.results.add(node.targets[0].id[-7:]+'L')
            else:
                self.results.add(node.targets[0].id+'L')
        else:
            self.results.add(node.targets[0].id)

    

    def visit_FunctionDef(self, node):
        for contents in node.body:
            if isinstance(contents, ast.Return):
                if len(node.name) > 4:
                    self.results.add(node.name[-4:]+'Ret')
                else:
                    self.results.add(node.name+'Ret')

        if node.args.args:
            for i in range(len(node.args.args)):
                self.results.add(node.args.args[i].arg+'N')
        for contents in node.body:
            self.visit(contents)
        
        
        
