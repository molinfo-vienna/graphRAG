import os
import glob
import ast
import re
import tokenize
from io import StringIO
from ClassAndFunctionVisitor import ClassAndFunctionVisitor

class DocParser(): 

    def __init__(self, dir_path: str, all_files_info: dict = {}) -> None:
        self.dir_path = dir_path    # path to directory that should be parsed
        self.all_files_info = all_files_info    # dict with parsed information

    def parse_dir(self) -> dict:
        # parses files within the dir_path into the all_files_info_dict
        file_pattern = os.path.join(self.dir_path, '*.doc.py')  # only parse .doc.py files
        file_list = glob.glob(file_pattern)
        folder = self.extract_cdpl_substring(self.dir_path)
        self.all_files_info[folder] = {}    # the folder names are the keys
        self.parse_files(file_list, folder)
        return self.all_files_info
    
    def parse_files(self, file_list: list, folder: str) -> None:
        # parse classes and functions from files
        unreadable_files = 0    # Some files contain syntax errors 
        for file_path in file_list: # Loop through each file in the list
            with open(file_path, 'r') as f: # Open and read the text file
                content = f.read()
                comments = self.extract_comments(content)
            try: 
                tree = ast.parse(content) # get an AST tree from the content of the doc.py file
            except SyntaxError as e:
                try:
                    content = self.clean_unreadable_text(content)   # there are syntax errors in the documentation
                    tree = ast.parse(content)
                except SyntaxError as e: 
                    print(f'Syntax error in file {file_path}: {e}') 
                    unreadable_files = unreadable_files + 1
                    continue 

            visitor = ClassAndFunctionVisitor(comments) # Create an instance of the ClassAndFunctionVisitor and visit the AST
            visitor.visit(tree)
            file_name = self.extract_doc_py_filename(file_path) # get the name of the file
            self.all_files_info[folder][file_name] = {"classes": visitor.classes, "functions": visitor.functions }
        print(f"Amount of files that could not be parsed: {unreadable_files}")

    
    def extract_comments(self, text: str) -> list:
        # Identifies the comments in the text and returns them
        comments = []
        tokens = tokenize.generate_tokens(StringIO(text).readline)
        for tok_type, tok_string, start, _, _ in tokens:
            if tok_type == tokenize.COMMENT:
                comments.append((start[0], tok_string.strip()))
        return comments

    def clean_unreadable_text(self, text: str) -> str:
        # trys out all the encountered syntax errors and attempts to solve them
        text = self.replace_naming_clash(text)
        text = self.remove_empty_colon_parameters(text)
        text = self.insert_default_strings(text)
        return text

    def extract_cdpl_substring(self, path: str) -> str | None:
        # Regular expression to find the substring after 'CDPL/' until the next '/'
        match = re.search(r'CDPL/([^/]+)', path)
        if match:
            return match.group(1)
        return None

    def extract_doc_py_filename(self, path: str) -> str | None:
        # Regular expression to find filenames that end with '.doc.py'
        match = re.search(r'([^/]+\.doc\.py)$', path)
        if match:
            return match.group(1)
        return None

    def replace_naming_clash(self, text: str) -> str:
        # Regular expression to find 'is' within parentheses and replace it with 'stream'
        return re.sub(r'\(([^)]*?)\bis\b([^)]*?)\)', lambda match: f'({match.group(1)}stream{match.group(2)})', text)

    def remove_empty_colon_parameters(self, text: str) -> str:
        # Remove function parameters that are just a colon
        return re.sub(r'\(\s*:\s*\)', '()', text)

    def insert_default_strings(self, text: str) -> str:
        # Insert an = where there are default parameters with '' directly after the parameter name 
        def replacer(match):
            before = match.group(1)
            default_str = match.group(2)
            after = match.group(3)
            return f"({before}={default_str}{after})"
        return re.sub(r"\(\s*([^)]*?mime_type)('[^=)]*?')([^)]*?)\)", replacer, text)


if __name__ == "__main__":
    chem_folder_path = "/data/shared/projects/graphRAG/CDPKit/Doc/Doxygen/Python-API/Source/CDPL/Chem"
    pharm_folder_path = "/data/shared/projects/graphRAG/CDPKit/Doc/Doxygen/Python-API/Source/CDPL/Pharm"
    all_files_info = DocParser(chem_folder_path).parse_dir()
    all_files_info = DocParser(pharm_folder_path, all_files_info).parse_dir()
    all_files_info

