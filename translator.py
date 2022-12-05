import argparse
import ast
from visitors.GlobalVariables import GlobalVariableExtraction
from visitors.LocalVariables import LocalVariableExtraction
from visitors.TopLevelProgram import TopLevelProgram
from visitors.FunctionVisitor import FunctionVisitor
from generators.StaticMemoryAllocation import StaticMemoryAllocation
from generators.LocalMemoryAllocation import LocalMemoryAllocation
from generators.EntryPoint import EntryPoint
from generators.FuncEntryPoint import FuncEntryPoint

def main():
    input_file, print_ast = process_cli()
    with open(input_file) as f:
        source = f.read()
    node = ast.parse(source)
    if print_ast:
        print(ast.dump(node, indent=2))
    else:
        process(input_file, node)
    
def process_cli():
    """"Process Command Line Interface options"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', help='filename to compile (.py)')
    parser.add_argument('--ast-only', default=False, action='store_true')
    args = vars(parser.parse_args())
    return args['f'], args['ast_only']

def process(input_file, root_node):
    print(f'; Translating {input_file}')
    extractor = GlobalVariableExtraction()
    extractor.visit(root_node)
    memory_alloc = StaticMemoryAllocation(extractor.results)
    print('; Branching to top level (tl) instructions')
    print('\t\tBR tl')
    memory_alloc.generate()
    top_level = TopLevelProgram('tl')
    top_level.visit(root_node)
    ep = EntryPoint(top_level.finalize())
    for s in root_node.body:
            if isinstance(s, ast.FunctionDef):
                local_ext = LocalVariableExtraction()
                local_ext.visit(s)
                top_level.local_vars = local_ext.results
                func_process(s)
                top_level.local_vars = None
    ep.generate() 

def func_process(funcdef_node):
    print(f'; ***** {funcdef_node.name} function definition')
    extractor = LocalVariableExtraction()
    extractor.visit(funcdef_node)
    memory_alloc = LocalMemoryAllocation(extractor.results)
    memory_alloc.generate()
    func_level = FunctionVisitor(f'{funcdef_node.name}',extractor)
    func_level.visit(funcdef_node)
    ep_func = FuncEntryPoint(func_level.finalize())
    ep_func.generate()
    
if __name__ == '__main__':
    main()
