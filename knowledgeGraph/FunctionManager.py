from neo4j import Driver, Transaction
from DecoratorManager import DecoratorManager
from ParameterManager import ParameterManager
from TypeManager import TypeManager
import json

class FunctionManager(): 
    def __init__(self, driver: Driver|None = None, info_dict: dict|None = None):
        self.driver = driver 
        self.info_dict = info_dict
        self.DecoratorManager = DecoratorManager()
        self.ParameterManager = ParameterManager()
        self.TypeManager = TypeManager()

    def create_functions(self) -> None: 
        with self.driver.session() as session:
            session.execute_write(self._create_functions)

    def _create_functions(self, tx: Transaction) -> None:
        for nested_dict in self.info_dict.values():
            for file_name, class_and_function_dicts in nested_dict.items():
                for f in class_and_function_dicts["functions"]:
                    # loops through all functions declared in the files and creates the nodes and relationships 
                    function_name = f["name"]
                    function_comment = f["comment"]
                    parameter_dict = json.dumps(self.ParameterManager._parse_parameters(f["params"]))
                    function_decorators = json.dumps(f["decorators"])
                    function_return_type = json.dumps(f["return_type"])
                    self._create_function_node(tx, function_name, function_comment, parameter_dict, function_decorators, function_return_type)
                    self._create_function_file_relationship(tx, function_name, function_comment, parameter_dict, function_decorators, function_return_type, file_name)
                    self._create_function_inputs(tx, f)

    def _create_function_node(self, tx: Transaction, function_name: str, function_comment: str,
                              parameter_dict: str, decorator_list: str, return_type: str) -> None:
        # creates the node of the function (if it does not already exist)
        query = """
        MERGE (f:Function {name: $function_name, comment: $function_comment, parameter: $parameter_dict, decorators: $decorator_list, returns: $return_type})
        RETURN f
        """
        tx.run(query, function_name=function_name, function_comment=function_comment, parameter_dict=parameter_dict, decorator_list=decorator_list, return_type=return_type)

    def _create_function_file_relationship(self, tx: Transaction, function_name: str, function_comment: str, 
                                           parameter_dict: str, decorator_list: str, return_type: str, file_name: str) -> None: 
        # creates the relationship between a function and the file it is declared at (if it does not already exist)
        query = """
        MATCH (fo:File {name: $file_name}), (fi:Function {name: $function_name, comment: $function_comment, parameter: $parameter_dict, decorators: $decorator_list, returns: $return_type})
        MERGE (fi)-[:DECLARED_AT]->(fo)
        """
        tx.run(query, file_name=file_name, function_name=function_name, function_comment=function_comment, parameter_dict=parameter_dict, decorator_list=decorator_list, return_type=return_type)
    
    def _create_function_class_relationship(self, tx: Transaction, function_name: str, function_comment: str, 
                                            class_name: str, parameter_dict: str, decorator_list: str, return_type: str) -> None: 
        # if the function is a method in a class, it creates this relationship (if it does not already exist)
        query = """
        MATCH (fo:Class {name: $class_name}), (fi:Function {name: $function_name, comment: $function_comment, parameter: $parameter_dict, decorators: $decorator_list, returns: $return_type})
        MERGE (fo)-[:HAS]->(fi)
        """
        tx.run(query, class_name=class_name, function_name=function_name, function_comment=function_comment, parameter_dict=parameter_dict, decorator_list=decorator_list, return_type=return_type)

    def _create_function_inputs(self, tx: Transaction, function_dict: dict) -> None: 
        # creates the nodes and relationships for the function inputs
        from ClassManager import ClassManager
        function_name = function_dict["name"]
        function_comment = function_dict["comment"]
        parameter_dict = json.dumps(self.ParameterManager._parse_parameters(function_dict["params"]))
        function_decorators = json.dumps(function_dict["decorators"])
        function_return_type = json.dumps(function_dict["return_type"])
        for p in function_dict["params"]:
            parameter_name = p["name"]
            parameter_comment = p["comment"]
            parameter_type = json.dumps(p["type"])
            parameter_default = json.dumps(p["default"])
            self.ParameterManager._create_parameter_node(tx, parameter_name, parameter_comment, parameter_type, parameter_default) 
            self.ParameterManager._create_parameter_function_relationship(tx,  function_name, function_comment, parameter_dict, function_decorators, function_return_type, parameter_name, parameter_comment, parameter_type, parameter_default)
            type_name = parameter_type
            if "." in parameter_type: 
                modules = p["type"].split(".")
                type_name = modules[-1]
            ClassManager._create_class_node(tx, class_name=type_name)   # also creates class nodes for types
            self.TypeManager._create_type_relationship(tx, parameter_name, parameter_comment, parameter_type, parameter_default, type_name)

        for d in function_dict["decorators"]:
            self.DecoratorManager._create_decorator_node(tx, decorator_name=d)
            self.DecoratorManager._create_decorator_function_relationship(tx, d, function_name, function_comment, parameter_dict, function_decorators, function_return_type)



