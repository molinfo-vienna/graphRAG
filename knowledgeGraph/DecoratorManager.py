from neo4j import Transaction


class DecoratorManager(): 
    def _create_decorator_node(self, tx: Transaction, decorator_name: str) -> None: 
        # creates the decorator node (if it does not already exist)
        query = """
        MERGE (f:Decorator {name: $decorator_name})
        RETURN f
        """
        tx.run(query, decorator_name=decorator_name)
    
    def _create_decorator_class_relationship(self, tx: Transaction, class_name: str, decorator_name: str) -> None: 
        # creates the relationship between a class and its decorator (if it does not already exist)
        query = """
            MATCH (fo:Class {name: $class_name}), (fi:Decorator {name: $decorator_name})
            MERGE (fo)-[:HAS]->(fi)
            """
        tx.run(query, class_name=class_name, decorator_name=decorator_name)

    def _create_decorator_function_relationship(self, tx: Transaction, decorator_name: str, function_name: str, function_comment: str, 
                                                parameter_dict: str, decorator_list: str, return_type: str) -> None:
        # creates the relationship between a function and its decorator (if it does not already exist)
        query = """
        MATCH (fo:Function {name: $function_name, comment: $function_comment, parameter: $parameter_dict, decorators: $decorator_list, returns: $return_type}), (fi:Decorator {name: $decorator_name})
        MERGE (fo)-[:HAS]->(fi)
        """
        tx.run(query, decorator_name=decorator_name, function_name=function_name, function_comment=function_comment, parameter_dict=parameter_dict, decorator_list=decorator_list, return_type=return_type)

   