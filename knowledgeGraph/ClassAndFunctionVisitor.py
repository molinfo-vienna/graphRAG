import ast
import re


# Define a visitor class that will collect class and function information
class ClassAndFunctionVisitor(ast.NodeVisitor):
    # TO DO: Write tests
    def __init__(self, comments) -> None:
        self.classes = []
        self.functions = []
        self.comments = comments
        # stack to keep track of class_nesting
        self.class_stack = []
        super().__init__()

    def get_name(self, node): 
        if isinstance(node, ast.Name): 
            name = node.id
        elif isinstance(node, ast.Constant):
            name =str(node.value)
        elif isinstance(node, ast.Attribute): 
            name = self.get_name(node.value) + "." + node.attr
        elif isinstance(node, ast.Call):
            name = {"callable": self.get_name(node.func), "arguments": [self.get_name(arg) for arg in node.args]}
        else: 
            name = "No value"
        return name

    def parse_parameters(self, node, comments): 
        default_values = [self.get_name(d) for d in node.args.defaults]
        params_with_defaults = ["No default"] * (len(node.args.args) - len(default_values)) + default_values
        params = []
        for i, arg in enumerate(node.args.args):
            param_info = {
                "name": arg.arg,
                "type": self.get_name(arg.annotation),
                "default": params_with_defaults[i], 
                "comment": comments.get(arg.arg, "")
            }
            params.append(param_info)
        return params


    def parse_function(self, node):
        parsed_comments = self.parse_comments(node.lineno)
        return_type = self.get_name(node.returns)
        params = self.parse_parameters(node, parsed_comments["param"])
        return {
            'name': node.name,
            'params': params,
            "decorators": [self.get_name(d) for d in node.decorator_list],
            "return_type": {"type": return_type, "comment": parsed_comments.get("return", "")},
            "comment:": parsed_comments.get("brief", "")
        }
    
    def parse_attribute(self, node):
        parsed_comments = self.parse_comments(node.lineno)
        return {
            "name": node.targets[0].id,
            "value": self.get_name(node.value),
            "comment": parsed_comments.get("brief", "")
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

    def get_associated_comments(self, lineno): 
        associated_comments = []
        for line, comment in reversed(self.comments): 
            if line < lineno: 
                if comment.startswith("##"):
                    break
                if comment == "#": 
                    continue
                associated_comments.append(comment.strip("#").strip())
        associated_comments.reverse()
        return associated_comments


    def parse_comments(self, lineno):  
        associated_comments = self.get_associated_comments(lineno=lineno)
        parsed_comments = {"param": {}} 
        current_tag = None
        current_param = None

        for comment in associated_comments:
            if comment.startswith("\\brief"):
                current_tag = "brief"
                parsed_comments["brief"] = comment.strip("\\brief").strip()

            elif comment.startswith("\\param"):
                current_tag = "param"
                if len(comment.split()) > 1: 
                    current_param = comment.split()[1]
                else:
                    continue
                parsed_comments["param"][current_param] = comment.strip(f"\\param {current_param}").strip()

            elif comment.startswith("\\return"):
                current_tag = "return"
                parsed_comments["return"] = comment.strip("\\return").strip()

            else:
                if current_tag == "brief":
                    parsed_comments["brief"] += " " + comment.strip()  
                elif current_tag == "param" and current_param:
                    parsed_comments["param"][current_param] += " " + comment.strip()
                elif current_tag == "return":
                    parsed_comments["return"] += " " + comment.strip()

        return parsed_comments
            
    
    def parse_class(self, node): 
        parsed_comments = self.parse_comments(node.lineno)
        class_info = {
            'name': node.name,
            "bases": [self.get_name(b) for b in node.bases],
            "decorators": [self.get_name(d) for d in node.decorator_list],
            'methods': [],
            "class_attributes": [],
            "nested_classes": [], 
            "comment": parsed_comments.get("brief", "")
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
