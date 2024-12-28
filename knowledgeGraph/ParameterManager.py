from neo4j import Transaction

class ParameterManager(): 
    def _create_parameter_node(self, tx: Transaction, 
                               parameter_name: str, parameter_comment: str, parameter_type: str, parameter_default: str) -> None: 
        # creates the parameter node (if it does not already exist)
        query = """
        MERGE (f:Parameter {name: $param_name, comment: $parameter_comment, type: $type_name, default: $default_value})
        RETURN f
        """
        tx.run(query, param_name=parameter_name, parameter_comment=parameter_comment, type_name=parameter_type, default_value=parameter_default)
        
    def _create_parameter_function_relationship(self, tx: Transaction, function_name: str, function_comment: str, 
                                                parameter_dict: str, decorator_list: str, return_type: str, 
                                                parameter_name: str, parameter_comment: str, parameter_type: str, parameter_default: str) -> None: 
        # creates the relationship between an input parameter and its function (if it does not already exist)
        query = """
        MATCH (fo:Function {name: $function_name, comment: $function_comment, parameter: $parameter_dict, decorators: $decorator_list, returns: $return_type}), (fi:Parameter {name: $param_name, comment: $parameter_comment, type: $type_name, default: $default_value})
        MERGE (fo)-[:HAS]->(fi)
        """
        tx.run(query,function_name=function_name, function_comment=function_comment, parameter_dict=parameter_dict, decorator_list=decorator_list, return_type=return_type, param_name=parameter_name, parameter_comment=parameter_comment, type_name=parameter_type, default_value=parameter_default)

    def _parse_parameters(self, parameters: list) -> list: 
        parameters_list = []
        for p in parameters:
            parameters_list.append({key: value for key,value in p.items()})
        return parameters_list