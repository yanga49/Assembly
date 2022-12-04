import ast

LabeledInstruction = tuple[str, str]

class TopLevelProgram(ast.NodeVisitor):
    """We supports assignments and input/print calls"""

    def __init__(self, entry_point) -> None:
        super().__init__()
        self.__instructions = list()
        self.__record_instruction('NOP1', label=entry_point)
        self.__should_save = True
        self.__current_variable = None
        self.__elem_id = 0
        self.__first = dict()
        self.__symbol_table = dict()

    def finalize(self):
        self.__instructions.append((None, '.END'))
        return self.__instructions

    ####
    ## Handling Assignments (variable = ...)
    ####

    def visit_Assign(self, node):
        # remembering the name of the target
        self.__current_variable = node.targets[0].id
        # visiting the left part, now knowing where to store the result
        self.visit(node.value)
        node_value = node.value.__dict__
        name = self.__get_name(self.__current_variable)
        if self.__should_save:
            if self.is_constant(node.targets[0].id):  # skip STWA if constant
                pass
            elif 'value' not in node_value.keys():  # STWA if no known value
                self.__record_instruction(f'STWA {name},d')
            elif self.__first[node.targets[0].id]:  # skip STWA if first variable
                self.__first[node.targets[0].id] = False
            else:  # STWA if not first variable
                self.__record_instruction(f'STWA {name},d')
        else:
            self.__should_save = True
        self.__current_variable = None

    def visit_Constant(self, node):
        node_value = node.__dict__
        if 'name' not in node_value.keys():  # LDWA i when variable is modified
            self.__record_instruction(f'LDWA {node.value},i')
        elif self.is_constant(node_value['name']):  # skip LDWA if constant
            pass
        else:  # skip first LDWA for known variable and indicate to skip STWA
            self.__first[node_value['name']] = True

    def visit_Name(self, node):
        node_value = node.__dict__
        name = self.__get_name(node.id)
        if 'value' not in node_value.keys() and not self.is_constant(node.id):  # check not a Constant
            self.__record_instruction(f'LDWA {name},d')

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
                current_variable = self.__get_name(self.__current_variable)
                self.__record_instruction(f'DECI {current_variable},d')
                self.__should_save = False  # DECI already save the value in memory
            case 'print':
                # We are only supporting integers for now
                name = self.__get_name(node.args[0].id)
                self.__record_instruction(f'DECO {name},d')
            case _:
                raise ValueError(f'Unsupported function call: {node.func.id}')

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
        """We do not visit function definitions, they are not top level"""
        pass

    ####
    ## Helper functions to 
    ####

    def __record_instruction(self, instruction, label=None):
        self.__instructions.append((label, instruction))

    def __access_memory(self, node, instruction, label=None):
        if isinstance(node, ast.Constant):  # i instruction with value
            self.__record_instruction(f'{instruction} {node.value},i', label)
        elif self.is_constant(node.id):  # i instruction for constant
            name = self.__get_name(node.id)
            self.__record_instruction(f'{instruction} {name},i', label)
        else:  # d instruction
            name = self.__get_name(node.id)
            self.__record_instruction(f'{instruction} {name},d', label)

    def __identify(self):
        result = self.__elem_id
        self.__elem_id = self.__elem_id + 1
        return result

    def __get_name(self, name):  # records and returns 8 character name
        if type(name) is not str:
            return name
        if name not in self.__symbol_table.keys():
            if len(name) > 8:  # rename if len > 8
                self.__symbol_table[name] = name[0: 4] + name[-4:]
            else:
                self.__symbol_table[name] = name
        return self.__symbol_table[name]

    @staticmethod
    def is_constant(name: str):
        if name[0] == '_' and name[1:].isupper():
            return True
        else:
            return False
