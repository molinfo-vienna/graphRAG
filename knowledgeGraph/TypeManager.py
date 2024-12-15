from neo4j import Transaction

class TypeManager(): 
    def _create_type_relationship(self, tx: Transaction, 
                                  parameter_name: str, parameter_comment: str, parameter_type: str, parameter_default: str, 
                                  type_name: str) -> None:
        # creates the relationship between a parameter and its type (if it does not already exist)
        query = """
        MATCH (fo:Parameter {name: $param_name, comment: $parameter_comment, type: $parameter_type, default: $default_value}), (fi:Class {name: $type_name})
        MERGE (fo)-[:OF_TYPE]->(fi)
        """
        tx.run(query, param_name=parameter_name, parameter_comment=parameter_comment, parameter_type=parameter_type, type_name=type_name, default_value=parameter_default)