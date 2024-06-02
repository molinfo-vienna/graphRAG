from neo4j import GraphDatabase
import os
import glob
import ast
import re


# Define a visitor class that will collect class and function information
class ClassAndFunctionVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.classes = []
        self.functions = []
        # stack to keep track of class_nesting
        self.class_stack = []
        super().__init__()

    def get_name(self, node): 
        if isinstance(node, ast.Name): 
            name = node.id
        elif isinstance(node, ast.Constant):
            name = node.value
        elif isinstance(node, ast.Attribute): 
            name = self.get_name(node.value) + "." + node.attr
        elif isinstance(node, ast.Call):
            # TO DO: implement this 
            name = ""
        else: 
            name = ""
        return name

    def parse_parameters(self, node): 
        default_values = [self.get_name(d) for d in node.args.defaults]
        params_with_defaults = [""] * (len(node.args.args) - len(default_values)) + default_values
        params = []
        for i, arg in enumerate(node.args.args):
            param_info = {
                "name": arg.arg,
                "type": self.get_name(arg.annotation),
                "default": params_with_defaults[i]
            }
            params.append(param_info)
        return params


    def parse_function(self, node):
        return_type = self.get_name(node.returns)
        params = self.parse_parameters(node)
        return {
            'name': node.name,
            'params': params,
            "decorators": [self.get_name(d) for d in node.decorator_list],
            "return_type": return_type
        }
    
    def parse_attribute(self, node):
        return {
            "name": node.targets[0].id,
            "value": self.get_name(node.value)
        }
    
    def traverse_body(self, info, node): 
        for elem in node.body:
            if isinstance(elem, ast.FunctionDef):
                info['methods'].append(self.parse_function(elem))
            elif isinstance(elem, ast.Assign):
                info['class_attributes'].append(self.parse_attribute(elem))
            elif isinstance(elem, ast.ClassDef):
                nested_class_info = self.parse_class(elem)
                info['nested_classes'].append(nested_class_info)

    
    def parse_class(self, node): 
        class_info = {
            'name': node.name,
            "bases": [self.get_name(b) for b in node.bases],
            "decorators": [self.get_name(d) for d in node.decorator_list],
            'methods': [],
            "class_attributes": [],
            "nested_classes": []
        }
        self.traverse_body(class_info, node)
        return class_info

    def visit_ClassDef(self, node):
        self.class_stack.append(node.name)
        class_info = self.parse_class(node)
        if len(self.class_stack) == 1:  
            self.classes.append(class_info)
        self.generic_visit(node)
        self.class_stack.pop()
    
    def visit_FunctionDef(self, node):
        if not self.class_stack: 
            self.functions.append(self.parse_function(node))
        self.generic_visit(node)


def parse_files(path:str, all_files_info: dict):
    # TO DO: Shorten this 
    # TO DO: Parse docstrings/comments 
    file_pattern = os.path.join(path, '*.doc.py')
    file_list = glob.glob(file_pattern)
    folder = extract_cdpl_substring(path)
    all_files_info[folder] = {}
    unreadable_files = 0
    # Loop through each file in the list
    for file_path in file_list:
        # Open and read the text file
        with open(file_path, 'r') as f:
            content = f.read()
        try: 
            tree = ast.parse(content)
        except SyntaxError as e:
            try:
                content = clean_unreadable_text(content)
                if "DataFormat" in file_path:
                    content
                tree = ast.parse(content)
            except SyntaxError as e: 
                print(f'Syntax error in file {file_path}: {e}') 
                unreadable_files = unreadable_files + 1
                continue
            # TO DO: property() values for attributes, or in general ast.Call  

        # Create an instance of the visitor and visit the AST
        visitor = ClassAndFunctionVisitor()
        visitor.visit(tree)
        file_name = extract_doc_py_filename(file_path)
        all_files_info[folder][file_name] = {"classes": visitor.classes, "functions": visitor.functions }
    print(f"Amount of files that could not be parsed: {unreadable_files}")
    return all_files_info

def clean_unreadable_text(text):
    text = replace_naming_clash(text)
    text = remove_empty_colon_parameters(text)
    text = insert_default_strings(text)
    return text

def extract_cdpl_substring(path):
    # Regular expression to find the substring after 'CDPL/' until the next '/'
    match = re.search(r'CDPL/([^/]+)', path)
    if match:
        return match.group(1)
    return None

def extract_doc_py_filename(path):
    # Regular expression to find filenames that end with '.doc.py'
    match = re.search(r'([^/]+\.doc\.py)$', path)
    if match:
        return match.group(1)
    return None

def replace_naming_clash(text):
    # Regular expression to find 'is' within parentheses and replace it with 'stream'
    # The regex looks for 'is' surrounded by parentheses, possibly with other text
    return re.sub(r'\(([^)]*?)\bis\b([^)]*?)\)', lambda match: f'({match.group(1)}stream{match.group(2)})', text)

def remove_empty_colon_parameters(text):
    # Remove function parameters that are just a colon
    return re.sub(r'\(\s*:\s*\)', '()', text)

def insert_default_strings(text):
    def replacer(match):
        before = match.group(1)
        default_str = match.group(2)
        after = match.group(3)
        return f"({before}={default_str}{after})"
    # Insert an = where there are default parameters with '' directly after the parameter name 
    return re.sub(r"\(\s*([^)]*?mime_type)('[^=)]*?')([^)]*?)\)", replacer, text)


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
    all_files_info = {}
    all_files_info = parse_files(chem_folder_path, all_files_info)
    driver.close()

