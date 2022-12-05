import ast
from .LocalVariables import LocalVariableExtraction

LabeledInstruction = tuple[str, str]

class FunctionVisitor(ast.NodeVisitor):
    """We supports assignments and input/print calls"""

    def __init__(self, entry_point, local_vars: LocalVariableExtraction) -> None:
        super().__init__()
        self.local_vars = local_vars.results
        self.stack_alloc = len(self.local_vars)*2
        self.__instructions = list()
        self.__record_instruction('NOP1', label=entry_point)
        self.__should_save = True
        self.__current_variable = None
        self.__elem_id = 0

    def finalize(self):
        #self.__instructions.append((None, '.END'))
        return self.__instructions

    ####
    ## Handling Assignments (variable = ...)
    ####

    def visit_Assign(self, node):
        # remembering the name of the target
        self.__current_variable = node.targets[0].id
        # visiting the left part, now knowing where to store the result
        self.visit(node.value)
        if self.__should_save:
            self.__record_instruction(f'STWA {self.__current_variable},s')
        else:
            self.__should_save = True
        self.__current_variable = None


    def visit_Constant(self, node):
        self.__record_instruction(f'LDWA {node.value},i')
    
    def visit_Name(self, node):
        self.__record_instruction(f'LDWA {node.id},s')


    def visit_BinOp(self, node):
        self.__access_memory(node.left, 'LDWA')
        if isinstance(node.op, ast.Add):
            self.__access_memory(node.right, 'ADDA')
        elif isinstance(node.op, ast.Sub):
            self.__access_memory(node.right, 'SUBA')
        else:
            raise ValueError(f'Unsupported binary operator: {node.op}')

    def visit_Call(self, node):
        match node.func.id:
            case 'int': 
                # Let's visit whatever is casted into an int
                self.visit(node.args[0])
            case 'input':
                # We are only supporting integers for now
                self.__record_instruction(f'DECI {self.__current_variable},s')
                self.__should_save = False # DECI already save the value in memory
            case 'print':
                # We are only supporting integers for now
                self.__record_instruction(f'DECO {node.args[0].id},s')
            case _:
                self.__record_instruction(f'CALL {node.func.id}')
                #raise ValueError(f'Unsupported function call: { node.func.id}')

    ####
    ## Handling While loops (only variable OP variable)
    ####


    def visit_While(self, node):
        loop_id = self.__identify()
        loop_name = self.__get_name(loop_id)
        inverted = {
            ast.Lt: 'BRGE',  # '<'  in the code means we branch if '>=' 
            ast.LtE: 'BRGT',  # '<=' in the code means we branch if '>' 
            ast.Gt: 'BRLE',  # '>'  in the code means we branch if '<='
            ast.GtE: 'BRLT',  # '>=' in the code means we branch if '<'
            ast.NotEq: 'BREQ', # '=' in the code means we branch if '!='
            ast.Eq: 'BRNE' # '!=' in the code means we branch if '=='
        }
        # left part can only be a variable
        self.__access_memory(node.test.left, 'LDWA', label=f'test_{loop_name}')
        # right part can only be a variable
        self.__access_memory(node.test.comparators[0], 'CPWA')
        # Branching is condition is not true (thus, inverted)
        self.__record_instruction(f'{inverted[type(node.test.ops[0])]} end_l_{loop_name}')
        # Visiting the body of the loop
        for contents in node.body:
            self.visit(contents)
        self.__record_instruction(f'BR test_{loop_name}')
        # Sentinel marker for the end of the loop
        self.__record_instruction(f'NOP1', label=f'end_l_{loop_name}')
    

    def visit_If(self,node):
        cond_id = self.__identify()
        inverted = {
            ast.Lt:  'BRGE', # '<'  in the code means we branch if '>=' 
            ast.LtE: 'BRGT', # '<=' in the code means we branch if '>' 
            ast.Gt:  'BRLE', # '>'  in the code means we branch if '<='
            ast.GtE: 'BRLT', # '>=' in the code means we branch if '<'
            ast.NotEq: 'BREQ', # '=' in the code means we branch if '!='
            ast.Eq: 'BRNE' # '!=' in the code means we branch if '=='
        }
        # left part can only be a variable
        self.__access_memory(node.test.left, 'LDWA', label = f'if_{cond_id}')
        # right part can only be a variable
        self.__access_memory(node.test.comparators[0], 'CPWA')
        # Branching is condition is not true (thus, inverted)
    
        # Visiting the body of the loop
        
        if node.orelse:
            if isinstance(node.orelse[0], ast.If):
                self.__record_instruction(f'{inverted[type(node.test.ops[0])]} elif_{cond_id}')
            else: 
                self.__record_instruction(f'{inverted[type(node.test.ops[0])]} else_{cond_id}')

        for contents in node.body:
            self.visit(contents)
        self.__record_instruction(f'BR aft_{cond_id}')

        while node.orelse and len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            self.__record_instruction(f'NOP1', label = f'elif_{cond_id}')
            
            #self.__access_memory(node.test.left, 'LDWA', label = f'/elif_{cond_id}')
        # right part can only be a variable
            self.__access_memory(node.test.comparators[0], 'CPWA')
            self.__record_instruction(f'{inverted[type(node.test.ops[0])]} else_{cond_id}')
            node = node.orelse[0]
            self.visit(node.test)
            for content in node.body:
                self.visit(content)
            self.__record_instruction(f'BR aft_{cond_id}')
            
        if node.orelse:
            self.__record_instruction(f'NOP1', label = f'else_{cond_id}')
            for contents in node.orelse:
                self.visit(contents)
            self.__record_instruction(f'BR aft_{cond_id}')
        
        self.__record_instruction(f'BR aft_{cond_id}')
        self.__record_instruction(f'NOP1', label = f'aft_{cond_id}')


    ####
    ## Not handling function calls 
    ####

    def visit_FunctionDef(self, node):
        
        # if function is not a void, allocating space on the stack for return value
        for s in node.body:
            if isinstance(s, ast.Return):
                self.__record_instruction(f'.EQUATE {self.stack_alloc + 2}', label = f'retVal')
        
        # if node.args.args:
        #     for i in range(len(node.args.args)):
        #         self.__record_instruction(f'.EQUATE (2nd last stack pos)', label = f'{node.args.args[i].arg}')

        self.__record_instruction(f'SUBSP {self.stack_alloc},i')
        for contents in node.body:
            self.visit(contents)
        self.__record_instruction(f'ADDSP {self.stack_alloc},i')
        self.__record_instruction(f'RET')
        
    def visit_Return(self, node):
        self.__record_instruction(f'STWA retVal,s')



    ####
    ## Helper functions to 
    ####

    def __record_instruction(self, instruction, label = None):
        self.__instructions.append((label, instruction))

    def __access_memory(self, node, instruction, label = None):
        if isinstance(node, ast.Constant):
            self.__record_instruction(f'{instruction} {node.value},i', label)
        # if node is a constant with a name (.EQUATE) keyword 
        elif node.id[0] == '_': 
            self.__record_instruction(f'{instruction} {node.id},i', label)
        else:
            self.__record_instruction(f'{instruction} {node.id},s', label)

    def __identify(self):
        result = self.__elem_id
        self.__elem_id = self.__elem_id + 1
        return result

