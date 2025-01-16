import ast


# Visitor class that will collect class and function information from the AST
class ClassAndFunctionVisitor(ast.NodeVisitor):
    def __init__(self, comments: list) -> None:
        self.classes = []
        self.functions = []
        self.comments = comments
        self.class_stack = [] # stack to keep track of nested classes
        super().__init__() # inherits the base functionalities of ast.NodeVisitor

    def get_name(self, node) -> str: 
        # parses the name of the node depending on the node type
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

    def parse_parameters(self, node, comments: list) -> list: 
        # parses the input parameters of a function
        default_values = [self.get_name(d) for d in node.args.defaults]
        params_with_defaults = ["No default"] * (len(node.args.args) - len(default_values)) + default_values    # add default values
        params = []
        for i, arg in enumerate(node.args.args):
            param_info = {
                "name": arg.arg,
                "type": self.get_name(arg.annotation),
                "default": params_with_defaults[i], 
                "comment": comments.get(arg.arg, "")    # if there is no comment, an empty string is added 
            }
            params.append(param_info)
        return params


    def parse_function(self, node) -> dict:
        parsed_comments = self.parse_comments(node.lineno)
        return_type = self.get_name(node.returns)
        params = self.parse_parameters(node, parsed_comments["param"])
        return {
            'name': node.name,
            'params': params,
            "decorators": [self.get_name(d) for d in node.decorator_list],
            "return_type": {"type": return_type, "comment": parsed_comments.get("return", "")},
            "comment": parsed_comments.get("brief", "")
        }
    
    def parse_attribute(self, node) -> dict:
        parsed_comments = self.parse_comments(node.lineno)
        return {
            "name": node.targets[0].id,
            "value": self.get_name(node.value),
            "comment": parsed_comments.get("brief", "")
        }
    
    def traverse_body(self, info: dict, node): 
        # traverses the body of a node and parses the child nodes
        for elem in node.body:
            if isinstance(elem, ast.FunctionDef):
                info['methods'].append(self.parse_function(elem))
            elif isinstance(elem, ast.Assign):
                info['class_attributes'].append(self.parse_attribute(elem))
            elif isinstance(elem, ast.ClassDef):
                nested_class_info = self.parse_class(elem)
                info['nested_classes'].append(nested_class_info)

    def get_associated_comments(self, lineno: int) -> list: 
        # gets the comments that belong to a specific node within the AST
        associated_comments = []
        for line, comment in reversed(self.comments):   # start from the bottom
            if line < lineno:   # look at the comments directly above the class/function etc.
                if comment.startswith("##"): # marks the end of the comment belonging to this node
                    break
                if comment == "#": 
                    continue
                associated_comments.append(comment.strip("#").strip())  # remove the unnecessary whitespace and #
        associated_comments.reverse()   # need to reverse as we started from the bottom 
        return associated_comments


    def parse_comments(self, lineno: int) -> dict:  
        associated_comments = self.get_associated_comments(lineno=lineno)
        parsed_comments = {"param": {}} 
        current_tag = None
        current_param = None

        for comment in associated_comments:
            # the comments start with certain tags that indicate what they will describe
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
                # comments will go over multiple lines
                if current_tag == "brief":
                    parsed_comments["brief"] += " " + comment.strip()  
                elif current_tag == "param" and current_param:
                    parsed_comments["param"][current_param] += " " + comment.strip()
                elif current_tag == "return":
                    parsed_comments["return"] += " " + comment.strip()

        return parsed_comments
            
    
    def parse_class(self, node) -> dict: 
        parsed_comments = self.parse_comments(node.lineno)  # get associated comments
        class_info = {
            'name': node.name,
            "bases": [self.get_name(b) for b in node.bases],    # base it inherits from
            "decorators": [self.get_name(d) for d in node.decorator_list],
            'methods': [],
            "class_attributes": [],
            "nested_classes": [], 
            "comment": parsed_comments.get("brief", "")
        }
        self.traverse_body(class_info, node)
        return class_info

    def visit_ClassDef(self, node) -> None: 
        # needed to overwrite the default function from ast
        self.class_stack.append(node.name)  # handles nested classes
        class_info = self.parse_class(node)
        if len(self.class_stack) == 1:  
            self.classes.append(class_info)
        self.generic_visit(node)
        self.class_stack.pop()
    
    def visit_FunctionDef(self, node) -> None:
        # needed to overwrite the default function from ast
        if not self.class_stack: 
            self.functions.append(self.parse_function(node))
        self.generic_visit(node)
