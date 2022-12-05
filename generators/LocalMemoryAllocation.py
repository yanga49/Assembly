import ast

class LocalMemoryAllocation(ast.NodeVisitor):

    def __init__(self, local_vars: dict()) -> None:
        self.__local_vars = local_vars

    def generate(self):
        print('; Allocating local variables on the stack')
        numvars = len(self.__local_vars)*2 - 2
        for n in self.__local_vars:
            print(f'{str(n+":"):<9}\t.EQUATE {numvars}') # reserving memory
            numvars -= 2
