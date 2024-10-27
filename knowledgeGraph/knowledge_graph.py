from neo4j import GraphDatabase
from DocParser import DocParser
import json


class ProjectManager(): 
    def __init__(self, driver, project_name: str) -> None:
        self.project_name = project_name
        self.driver = driver
    
    def create_project(self):
        with self.driver.session() as session:
            session.execute_write(self._create_project_node, self.project_name)

    def _create_project_node(self, tx, project_name):
        query = """
        MERGE (p:Project {name: $project_name})
        RETURN p
        """
        result = tx.run(query, project_name=project_name)
        return result.single()

class FolderManager():  
    def __init__(self, driver, info_dict, project_name):
        self.driver = driver
        self.info_dict = info_dict
        self.project_name = project_name
        
    def create_folders(self):
        with self.driver.session() as session:
            session.execute_write(self._create_folder_nodes_and_relationships, self.info_dict, self.project_name)


    def _create_folder_nodes_and_relationships(self, tx, info_dict, project_name):
         for folder in info_dict.keys():
             self._create_folder_nodes(tx, folder)
             self._create_folder_relationships(tx, project_name, folder)

    def _create_folder_nodes(self, tx, folder):
        query = """
        MERGE (f:Folder {name: $folder_name})
        RETURN f
        """
        tx.run(query, folder_name=folder)

    def _create_folder_relationships(self, tx, project_name, folder):
        query = """
        MATCH (p:Project {name: $project_name}), (f:Folder {name: $folder_name})
        MERGE (f)-[:INCLUDED_IN]->(p)
        """
        tx.run(query, project_name=project_name, folder_name=folder)

class FileManager():
    def __init__(self, driver, info_dict) -> None:
        self.driver = driver 
        self.info_dict = info_dict

    def create_files(self): 
        with self.driver.session() as session:
            session.execute_write(self._create_file_nodes_and_relationships)

    def _create_file_nodes_and_relationships(self, tx):
         for folder, nested_dict in self.info_dict.items():
             for file_name in nested_dict.keys():
                self._create_file_nodes(tx, file_name)
                self._create_file_relationships(tx, folder, file_name)

  
    def _create_file_nodes(self, tx, file_name):
        query = """
        MERGE (f:File {name: $file_name})
        RETURN f
        """
        tx.run(query, file_name=file_name)

    def _create_file_relationships(self, tx, folder, file_name):
        query = """
        MATCH (fo:Folder {name: $folder_name}), (fi:File {name: $file_name})
        MERGE (fi)-[:INCLUDED_IN]->(fo)
        """
        tx.run(query, folder_name=folder, file_name=file_name)

class FunctionManager(): 
    def __init__(self, driver = None, info_dict = None) -> None:
        self.driver = driver 
        self.info_dict = info_dict
        self.DecoratorManager = DecoratorManager()
        self.ParameterManager = ParameterManager()
        self.TypeManager = TypeManager()

    def create_functions(self): 
        with self.driver.session() as session:
            session.execute_write(self._create_functions)

    def _create_functions(self, tx):
        for nested_dict in self.info_dict.values():
            for file_name, class_and_function_dicts in nested_dict.items():
                for f in class_and_function_dicts["functions"]:
                    function_name = f["name"]
                    function_comment = f["comment"]
                    parameter_dict = json.dumps(self.ParameterManager._parse_parameters(f["params"]))
                    function_decorators = json.dumps(f["decorators"])
                    function_return_type = json.dumps(f["return_type"])
                    self._create_function_node(tx, function_name, function_comment, parameter_dict, function_decorators, function_return_type)
                    self._create_function_file_relationship(tx, function_name, function_comment, parameter_dict, function_decorators, function_return_type, file_name)
                    self._create_function_inputs(tx, f)

    def _create_function_node(self, tx, function_name, function_comment, parameter_dict, decorator_list, return_type):
        query = """
        MERGE (f:Function {name: $function_name, comment: $function_comment, parameter: $parameter_dict, decorators: $decorator_list, returns: $return_type})
        RETURN f
        """
        tx.run(query, function_name=function_name, function_comment=function_comment, parameter_dict=parameter_dict, decorator_list=decorator_list, return_type=return_type)

    def _create_function_file_relationship(self, tx, function_name, function_comment, parameter_dict, decorator_list, return_type, file_name): 
        query = """
        MATCH (fo:File {name: $file_name}), (fi:Function {name: $function_name, comment: $function_comment, parameter: $parameter_dict, decorators: $decorator_list, returns: $return_type})
        MERGE (fi)-[:DECLARED_AT]->(fo)
        """
        tx.run(query, file_name=file_name, function_name=function_name, function_comment=function_comment, parameter_dict=parameter_dict, decorator_list=decorator_list, return_type=return_type)
    
    def _create_function_class_relationship(self, tx, function_name, function_comment, class_name,parameter_dict, decorator_list, return_type): 
        query = """
        MATCH (fo:Class {name: $class_name}), (fi:Function {name: $function_name, comment: $function_comment, parameter: $parameter_dict, decorators: $decorator_list, returns: $return_type})
        MERGE (fo)-[:HAS]->(fi)
        """
        tx.run(query, class_name=class_name, function_name=function_name, function_comment=function_comment, parameter_dict=parameter_dict, decorator_list=decorator_list, return_type=return_type)

    def _create_function_inputs(self, tx, function_dict): 
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
            ClassManager._create_class_node(tx, class_name=type_name)
            self.TypeManager._create_type_relationship(tx, parameter_name, parameter_comment, parameter_type, parameter_default, type_name)

        for d in function_dict["decorators"]:
            self.DecoratorManager._create_decorator_node(tx, decorator_name=d)
            self.DecoratorManager._create_decorator_function_relationship(tx, d, function_name, function_comment, parameter_dict, function_decorators, function_return_type)

class ClassManager(): 
    # TO DO: Implement this cleaner
    def __init__(self, driver = None, info_dict = None) -> None:
        self.driver = driver 
        self.info_dict = info_dict
        self.FunctionManager = FunctionManager()
        self.DecoratorManager = DecoratorManager()

    def create_classes(self): 
        with self.driver.session() as session:
            session.execute_write(self._create_classes)

    def _create_classes(self, tx):
        for nested_dict in self.info_dict.values():
            for file_name, class_and_function_dicts in nested_dict.items():
                for c in class_and_function_dicts["classes"]: 
                    ClassManager._create_class_node(tx, c["name"])
                    self._set_class_comment(tx, c["name"], c["comment"])
                    self._create_class_relationships(tx, file_name, c)
                
    @staticmethod
    def _create_class_node(tx, class_name):
        query = """
        MERGE (f:Class {name: $class_name})
        RETURN f
        """
        tx.run(query, class_name=class_name)

    def _create_class_inheritance_relationship(self, tx, class_name, base_name):
        query = """
        MATCH (fo:Class {name: $class_name}), (fi:Class {name: $base_name})
        MERGE (fo)-[:INHERITS_FROM]->(fi)
        """
        tx.run(query, class_name=class_name, base_name=base_name)

    def _create_class_file_relationship(self, tx, file_name, class_name): 
        query = """
        MATCH (fo:File {name: $file_name}), (fi:Class {name: $class_name})
        MERGE (fi)-[:DECLARED_AT]->(fo)
        """
        tx.run(query, file_name=file_name, class_name=class_name)

    def _set_class_attributes(self, tx, class_name, attributes): 
        query = """
        MATCH (f:Class {name: $class_name})
        set f.attributes = $attributes
        RETURN f
        """
        tx.run(query, class_name=class_name, attributes=attributes)

    def _set_class_comment(self, tx, class_name, class_comment): 
        query = """
        MATCH (f:Class {name: $class_name})
        set f.comment = $class_comment
        RETURN f
        """
        tx.run(query, class_name=class_name, class_comment=class_comment)
   
    def _create_nested_class_relationship(self, tx, class_name, nested_class_name):
        query = """
        MATCH (fo:Class {name: $class_name}), (fi:Class {name: $nested_class_name})
        MERGE (fo)-[:HAS]->(fi)
        """
        tx.run(query, class_name=class_name, nested_class_name=nested_class_name)

    def _create_class_relationships(self, tx, file_name, c):
        class_name = c["name"]
        self._create_class_file_relationship(tx, file_name, class_name)

        for base in c["bases"]: 
            base_name = base
            if "." in base: 
                modules = base.split(".")
                base_name = modules[-1]
            ClassManager._create_class_node(tx, class_name=base_name)
            self._create_class_inheritance_relationship(tx, class_name=class_name, base_name=base_name) 

        for d in c["decorators"]:
            self.DecoratorManager._create_decorator_node(tx, decorator_name=d)
            self.DecoratorManager._create_decorator_class_relationship(tx, class_name=class_name, decorator_name=d)

        for m in c["methods"]:
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

class DecoratorManager(): 
    def _create_decorator_node(self, tx, decorator_name): 
        query = """
        MERGE (f:Decorator {name: $decorator_name})
        RETURN f
        """
        tx.run(query, decorator_name=decorator_name)
    
    def _create_decorator_class_relationship(self, tx, class_name, decorator_name): 
        query = """
            MATCH (fo:Class {name: $class_name}), (fi:Decorator {name: $decorator_name})
            MERGE (fo)-[:HAS]->(fi)
            """
        tx.run(query, class_name=class_name, decorator_name=decorator_name)

    def _create_decorator_function_relationship(self, tx, decorator_name, function_name, function_comment, parameter_dict, decorator_list, return_type):
        query = """
        MATCH (fo:Function {name: $function_name, comment: $function_comment, parameter: $parameter_dict, decorators: $decorator_list, returns: $return_type}), (fi:Decorator {name: $decorator_name})
        MERGE (fo)-[:HAS]->(fi)
        """
        tx.run(query, decorator_name=decorator_name, function_name=function_name, function_comment=function_comment, parameter_dict=parameter_dict, decorator_list=decorator_list, return_type=return_type)

class ParameterManager(): 
    def _create_parameter_node(self, tx, parameter_name, parameter_comment, parameter_type, parameter_default): 
        query = """
        MERGE (f:Parameter {name: $param_name, comment: $parameter_comment, type: $type_name, default: $default_value})
        RETURN f
        """
        tx.run(query, param_name=parameter_name, parameter_comment=parameter_comment, type_name=parameter_type, default_value=parameter_default)
        
    def _create_parameter_function_relationship(self, tx, function_name, function_comment, parameter_dict, decorator_list, return_type, parameter_name, parameter_comment, parameter_type, parameter_default): 
        query = """
        MATCH (fo:Function {name: $function_name, comment: $function_comment, parameter: $parameter_dict, decorators: $decorator_list, returns: $return_type}), (fi:Parameter {name: $param_name, comment: $parameter_comment, type: $type_name, default: $default_value})
        MERGE (fo)-[:HAS]->(fi)
        """
        tx.run(query,function_name=function_name, function_comment=function_comment, parameter_dict=parameter_dict, decorator_list=decorator_list, return_type=return_type, param_name=parameter_name, parameter_comment=parameter_comment, type_name=parameter_type, default_value=parameter_default)

    def _parse_parameters(self, parameters): 
        parameters_list = []
        for p in parameters:
            parameters_list.append({key: value for key,value in p.items()})
        return parameters_list

class TypeManager(): 
    def _create_type_relationship(self, tx, parameter_name, parameter_comment, parameter_type, parameter_default, type_name):
        query = """
        MATCH (fo:Parameter {name: $param_name, comment: $parameter_comment, type: $parameter_type, default: $default_value}), (fi:Class {name: $type_name})
        MERGE (fo)-[:OF_TYPE]->(fi)
        """
        tx.run(query, param_name=parameter_name, parameter_comment=parameter_comment, parameter_type=parameter_type, type_name=type_name, default_value=parameter_default)
   
class KnowledgeGraphManager(): 
    # TO DO: Consider adding relationship for return type etc 
    def __init__(self, uri, user, password, project_name, info_dict):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.project_manager = ProjectManager(self.driver, project_name)
        self.folder_manager = FolderManager(self.driver, info_dict, project_name)
        self.file_manager = FileManager(self.driver, info_dict )
        self.class_manager = ClassManager(self.driver, info_dict)
        self.function_manager = FunctionManager(self.driver, info_dict)
        self.info_dict = info_dict

    def close(self):
        self.driver.close()
    
    def create_graph(self):
        self.project_manager.create_project()
        self.folder_manager.create_folders()
        self.file_manager.create_files()
        self.class_manager.create_classes()
        self.function_manager.create_functions()

    def clean_database(self):
        with self.driver.session() as session:
            session.execute_write(self._clean_database)

    @staticmethod
    def _clean_database(tx):
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        tx.run(query)


if __name__ == "__main__":
    uri = "neo4j+s://4de35fba.databases.neo4j.io"  
    username = "neo4j"  
    password = "87YkRGzIftmB-QU8CvYcLNzHZeFAZkeEQpwtZTEa4PU"  
    root_path = "/data/shared/projects/graphRAG/CDPKit/Doc/Doxygen/Python-API/Source/CDPL/"
    cdp_folders = [root_path + "Chem",
                   root_path + "Pharm",
                   root_path + "Base", 
                   root_path + "Biomol",
                   root_path + "ConfGen",
                   root_path + "Descr",
                   root_path + "ForceField",
                   root_path + "GRAIL",
                   root_path + "Grid",
                   root_path + "Math",
                   root_path + "MolProp",
                   root_path + "Shape",
                   root_path + "Util",
                   root_path + "Vis"]
    for folder in cdp_folders: 
        all_files_info = DocParser(folder).parse_files()
        cdpkit_graph_manager = KnowledgeGraphManager(uri, username, password, project_name="CDPKit", info_dict=all_files_info)
        cdpkit_graph_manager.create_graph()
        cdpkit_graph_manager.close()

