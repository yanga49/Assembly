import ast

class LocalMemoryAllocation(ast.NodeVisitor):
# Responsible for local memory allocation of each function definition (printing equal statements)
    def __init__(self, local_vars: dict()) -> None:
        self.__local_vars = local_vars
        self.returns = False

    def generate(self):
        print('; Allocating local variables on the stack')
        returns = False
        numvars = len(self.__local_vars)*2 
        for var in self.__local_vars: # if function returns a value, we have to allocate space for it
            if  var.endswith('Ret'): 
                # allocating space on the stack for the return address
                numvars = len(self.__local_vars)*2 
                print(f'{str(var+":"):<9}\t.EQUATE 0') 
                returns = True
                self.returns = True
                
            
        for n in self.__local_vars:
            if n.endswith('N') and returns == True:
                numvars -= 2
                returns = False
            elif n.endswith('N') and returns == False:
                numvars -= 2
            if not n.endswith('Ret'):
                print(f'{str(n+":"):<9}\t.EQUATE {numvars}') # reserving memory
                numvars -= 2
          
             

            