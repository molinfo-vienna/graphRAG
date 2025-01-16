from neo4j import Driver, Transaction
from FunctionManager import FunctionManager
from DecoratorManager import DecoratorManager
import json

class ClassManager(): 
    def __init__(self, driver: Driver|None = None, info_dict: dict|None = None):
        self.driver = driver 
        self.info_dict = info_dict
        self.FunctionManager = FunctionManager()
        self.DecoratorManager = DecoratorManager()

    def create_classes(self) -> None: 
        with self.driver.session() as session:
            session.execute_write(self._create_classes)

    def _create_classes(self, tx: Transaction) -> None:
        for nested_dict in self.info_dict.values():
            for file_name, class_and_function_dicts in nested_dict.items():
                # loops through all the classes in all files and creates their nodes and edges
                for c in class_and_function_dicts["classes"]: 
                    ClassManager._create_class_node(tx, c["name"])
                    self._set_class_comment(tx, c["name"], c["comment"])    # this is necessary if the class already exists but without a comment
                    self._create_class_relationships(tx, file_name, c)
                
    @staticmethod
    def _create_class_node(tx: Transaction, class_name: str) -> None:
        # creates a class node if it does not already exist
        query = """
        MERGE (f:Class {name: $class_name})
        RETURN f
        """
        tx.run(query, class_name=class_name)

    def _create_class_inheritance_relationship(self, tx: Transaction, class_name: str, base_name: str) -> None:
        # creates the relationship between a class and the class it inherits from (if it not already exists)
        query = """
        MATCH (fo:Class {name: $class_name}), (fi:Class {name: $base_name})
        MERGE (fo)-[:INHERITS_FROM]->(fi)
        """
        tx.run(query, class_name=class_name, base_name=base_name)

    def _create_class_file_relationship(self, tx: Transaction, file_name: str, class_name: str) -> None:
        # creates the relationship between a class and the file it is declared at (if it not already exists) 
        query = """
        MATCH (fo:File {name: $file_name}), (fi:Class {name: $class_name})
        MERGE (fi)-[:DECLARED_AT]->(fo)
        """
        tx.run(query, file_name=file_name, class_name=class_name)

    def _set_class_attributes(self, tx: Transaction, class_name: str, attributes: str) -> None: 
        # sets attributes of the class node 
        query = """
        MATCH (f:Class {name: $class_name})
        set f.attributes = $attributes
        RETURN f
        """
        tx.run(query, class_name=class_name, attributes=attributes)

    def _set_class_comment(self, tx: Transaction, class_name: str, class_comment: str) -> None: 
        # sets the comment of the class node
        query = """
        MATCH (f:Class {name: $class_name})
        set f.comment = $class_comment
        RETURN f
        """
        tx.run(query, class_name=class_name, class_comment=class_comment)
   
    def _create_nested_class_relationship(self, tx: Transaction, class_name: str, nested_class_name: str) -> None:
        # creates the relationship between a class and its nested class (if it not already exists)
        query = """
        MATCH (fo:Class {name: $class_name}), (fi:Class {name: $nested_class_name})
        MERGE (fo)-[:HAS]->(fi)
        """
        tx.run(query, class_name=class_name, nested_class_name=nested_class_name)

    def _create_class_relationships(self, tx: Transaction, file_name: str, c: dict) -> None:
        # takes a class dict and creates all relationships and nodes related to that class
        class_name = c["name"]
        self._create_class_file_relationship(tx, file_name, class_name)

        for base in c["bases"]: 
            base_name = base
            if "." in base: 
                modules = base.split(".")
                base_name = modules[-1]
            ClassManager._create_class_node(tx, class_name=base_name)   # this is why comments and attributes can be also set later if a class node was already created through inheritance
            self._create_class_inheritance_relationship(tx, class_name=class_name, base_name=base_name) 

        for d in c["decorators"]:
            self.DecoratorManager._create_decorator_node(tx, decorator_name=d)
            self.DecoratorManager._create_decorator_class_relationship(tx, class_name=class_name, decorator_name=d)

        for m in c["methods"]:
            # a method is treated the same way as a normal function definition, but it has a relationship to the class node
            method_name = m["name"]
            method_comment = m["comment"]
            parameters = json.dumps(self.FunctionManager.ParameterManager._parse_parameters(m["params"]))
            self.FunctionManager._create_function_node(tx, method_name, method_comment, parameters, json.dumps(m["decorators"]), return_type=json.dumps(m["return_type"]))
            self.FunctionManager._create_function_class_relationship(tx, method_name, method_comment, class_name, parameters, json.dumps(m["decorators"]), return_type=json.dumps(m["return_type"]))
            self.FunctionManager._create_function_inputs(tx, m)

        if c["class_attributes"]: 
            self._set_class_attributes(tx, class_name, json.dumps(c["class_attributes"]))

        for nc in c["nested_classes"]:
            ClassManager._create_class_node(tx, class_name=nc["name"])
            self._set_class_comment(tx, nc["name"], nc["comment"])
            self._create_class_relationships(tx, file_name=file_name, c=nc)
            self._create_nested_class_relationship(tx, class_name=class_name, nested_class_name=nc["name"])