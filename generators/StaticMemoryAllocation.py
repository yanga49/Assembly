
class StaticMemoryAllocation():

    def __init__(self, global_vars: dict()) -> None:
        self.__global_vars = global_vars
        self.__symbol_table = dict()

    def generate(self):
        print('; Allocating Global (static) memory')
        for n in self.__global_vars.keys():
            name = self.__get_name(n)
            if name[-1] == '_':
                print(f'{str(name + ":"):<9}\t.BLOCK {2 * self.__global_vars[n]}')  # reserving memory for array
            elif self.__global_vars[n] is None:
                print(f'{str(name + ":"):<9}\t.BLOCK 2')  # reserving memory for undefined variable
            elif self.is_constant(n):
                print(f'{str(name + ":"):<9}\t.EQUATE {self.__global_vars[n]}')  # reserving memory for constant
            else:
                print(f'{str(name + ":"):<9}\t.WORD {self.__global_vars[n]}')  # reserving memory for variable

    def __get_name(self, name: str):
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
