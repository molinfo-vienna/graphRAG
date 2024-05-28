from neo4j import GraphDatabase
import os
import glob
import ast


RESERVED_KEYWORDS = {
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break',
    'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally',
    'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal',
    'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
}



# Define a visitor class that will collect class and function information
class ClassAndFunctionVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.classes = []
        self.functions = []
        # signal if a function is a method within a class 
        self. within_class = False
        super().__init__()

    def parse_function(self, node):
        return {
            'name': node.name,
            'params': [{"name": arg.arg, "type": arg.annotation.id} for arg in node.args.args],
        }
    
    def parse_class(self, node): 
        class_info = {
            'name': node.name,
            "bases": node.bases[0].id if isinstance(node.bases[0], ast.Name) else "",
            'methods': []
        }
        for elem in node.body:
            if isinstance(elem, ast.FunctionDef):
                class_info['methods'].append(self.parse_function(elem))
        return class_info

    def visit_ClassDef(self, node):
        self.within_class = True
        class_info = self.parse_class(node)
        self.classes.append(class_info)
        self.generic_visit(node)
        self.within_class = False 
    
    def visit_FunctionDef(self, node):
        if self.within_class: 
            self.generic_visit(node)
            return
        self.functions.append(self.parse_function(node))
        self.generic_visit(node)


def parse_files(path:str):
    file_pattern = os.path.join(path, '*.doc.py')
    file_list = glob.glob(file_pattern)
    all_files_info = {"classes": [], "functions": []}
    # Loop through each file in the list
    for file_path in file_list:
        # Open and read the text file
        with open(file_path, 'r') as f:
            content = f.read()
        try: 
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f'Syntax error in file {file_path}: {e}') 
            # need to implement how to handle it if there is a reserved keyword used in the code
            continue
        # Create an instance of the visitor and visit the AST
        visitor = ClassAndFunctionVisitor()
        visitor.visit(tree)
        all_files_info["classes"].extend(visitor.classes)
        all_files_info["functions"].extend(visitor.functions)

'''
def create_graph(tx):
    # Create nodes with labels
    tx.run("CREATE (a:Class {name: 'Tautomer'})")
    tx.run("CREATE (b:Function {name: 'create'})")
    
    # Create relationship
    tx.run("MATCH (a:Class {name: 'Tautomer'}), (b:Function {name: 'create'}) "
           "CREATE (a)-[:HAS]->(b)")
    
def get_people():
    result = tx.run("MATCH (p:Function) RETURN p.name AS name")
    return [(record["name"]) for record in result]


def main(mode:str):
    if mode == "write": 
        with driver.session() as session:
            session.execute_write(create_graph)
    if mode == "read": 
        with driver.session() as session:
            functions = session.execute_read(get_people)
            print(functions)  # Output the list of people in the graph
'''

if __name__ == "__main__":
    uri = "neo4j+s://92611c46.databases.neo4j.io"  
    username = "neo4j"  
    password = "TkKpzBg85DBE3xtJDzKlA-J8s-g-vLkMknVN6hcc_ew"  
    driver = GraphDatabase.driver(uri, auth=(username, password))

    chem_folder_path = "/data/shared/projects/graphRAG/CDPKit/Doc/Doxygen/Python-API/Source/CDPL/Chem"
    parse_files(chem_folder_path)
    driver.close()

