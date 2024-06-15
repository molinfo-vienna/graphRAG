import os
import glob
import ast
import re
from knowledgeGraph import ClassAndFunctionVisitor

def parse_files(path:str, all_files_info: dict):
    # TO DO: Shorten this 
    # TO DO: Parse docstrings/comments 
    # TO DO: maybe turn this into a class
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
                tree = ast.parse(content)
            except SyntaxError as e: 
                print(f'Syntax error in file {file_path}: {e}') 
                unreadable_files = unreadable_files + 1
                continue 

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


if __name__ == "__main__":
    chem_folder_path = "/data/shared/projects/graphRAG/CDPKit/Doc/Doxygen/Python-API/Source/CDPL/Chem"
    pharm_folder_path = "/data/shared/projects/graphRAG/CDPKit/Doc/Doxygen/Python-API/Source/CDPL/Pharm"
    all_files_info = {}
    all_files_info = parse_files(chem_folder_path, all_files_info)
    all_files_info = parse_files(pharm_folder_path, all_files_info)
    all_files_info

