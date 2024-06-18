from neo4j import GraphDatabase
from DocParser import DocParser


class ProjectManager(): 
    def __init__(self, driver, project_name: str) -> None:
        self.project_name = project_name
        self.driver = driver
    
    def create_project(self):
        with self.driver.session() as session:
            session.execute_write(self._create_project_node, self.project_name)

    @staticmethod
    def _create_project_node(tx, project_name):
        query = """
        CREATE (p:Project {name: $project_name})
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

    @staticmethod
    def _create_folder_nodes(tx, folder):
        query = """
        CREATE (f:Folder {name: $folder_name})
        RETURN f
        """
        tx.run(query, folder_name=folder)

    @staticmethod
    def _create_folder_relationships(tx, project_name, folder):
        query = """
        MATCH (p:Project {name: $project_name}), (f:Folder {name: $folder_name})
        CREATE (f)-[:INCLUDED_IN]->(p)
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

    @staticmethod
    def _create_file_nodes(tx, file_name):
        query = """
        CREATE (f:File {name: $file_name})
        RETURN f
        """
        tx.run(query, file_name=file_name)

    @staticmethod
    def _create_file_relationships(tx, folder, file_name):
        query = """
        MATCH (fo:Folder {name: $folder_name}), (fi:File {name: $file_name})
        CREATE (fi)-[:INCLUDED_IN]->(fo)
        """
        tx.run(query, folder_name=folder, file_name=file_name)

class ClassAndFunctionManager(): 
    # TO DO: Implement this cleaner
    # TO DO: Implement full hierarchy
    # TO DO: prevent too many nodes and relationships 
    def __init__(self, driver, info_dict) -> None:
        self.driver = driver 
        self.info_dict = info_dict

    def create_classes_and_functions(self): 
        with self.driver.session() as session:
            session.execute_write(self._create_class_and_function_nodes_and_relationships)

    def _create_class_and_function_nodes_and_relationships(self, tx):
        for nested_dict in self.info_dict.values():
            for class_and_function_dicts in nested_dict.values():
                for c in class_and_function_dicts["classes"]: 
                    self._create_class_nodes(tx, c)
                for f in class_and_function_dicts["functions"]:
                    self._create_function_nodes(tx, f)

        for nested_dict in self.info_dict.values():
             for file_name, class_and_function_dicts in nested_dict.items():
                for c in class_and_function_dicts["classes"]: 
                    self._create_class_relationships(tx, file_name, c)
                
    @staticmethod
    def _create_class_nodes(tx, c):
        query = """
        CREATE (f:Class {name: $class_name})
        RETURN f
        """
        tx.run(query, class_name=c["name"])

    @staticmethod
    def _create_class_relationships(tx, file_name, c):
        query = """
        MATCH (fo:File {name: $file_name}), (fi:Class {name: $class_name})
        CREATE (fi)-[:DECLARED_AT]->(fo)
        """
        tx.run(query, file_name=file_name, class_name=c["name"])

        for b in c["bases"]: 
            # Check if the node exists
            check_query = """
            MATCH (f:Class {name: $base_name})
            RETURN f
            """
            result = tx.run(check_query, base_name=b).single()
    
            # If the node does not exist, create it
            if not result:
                create_query = """
                CREATE (f:Class {name: $base_name})
                RETURN f
                """
                tx.run(create_query, base_name=b)
        
            query = """
            MATCH (fo:Class {name: $class_name}), (fi:Class {name: $base_name})
            CREATE (fo)-[:INHERITS_FROM]->(fi)
            """
            tx.run(query, class_name=c["name"], base_name=b)

        for d in c["decorators"]:
            query = """
            MERGE (f:Decorator {name: $decorator_name})
            RETURN f
            """
            tx.run(query, decorator_name=d)

            query = """
            MATCH (fo:Class {name: $class_name}), (fi:Decorator {name: $decorator_name})
            CREATE (fo)-[:HAS]->(fi)
            """
            tx.run(query, class_name=c["name"], decorator_name=d)

        for m in c["methods"]:
            query = """
            CREATE (f:Method {name: $method_name})
            RETURN f
            """
            tx.run(query, method_name=m["name"])

            query = """
            MATCH (fo:Class {name: $class_name}), (fi:Method {name: $method_name})
            CREATE (fo)-[:HAS]->(fi)
            """
            tx.run(query, class_name=c["name"], method_name=m["name"])

            for p in m["params"]:
                query = """
                CREATE (f:Parameter {name: $param_name})
                RETURN f
                """
                tx.run(query, param_name=p["name"])
                
                # implement type
                # implement default 

            for d in m["decorators"]:
                query = """
                MERGE (f:Decorator {name: $decorator_name})
                RETURN f
                """
                tx.run(query, decorator_name=d)

                query = """
                MATCH (fo:Method {name: $method_name}), (fi:Decorator {name: $decorator_name})
                CREATE (fo)-[:HAS]->(fi)
                """
                tx.run(query, method_name=m["name"], decorator_name=d)

    @staticmethod
    def _create_function_nodes(tx, f):
        query = """
        CREATE (f:Function {name: $function_name})
        RETURN f
        """
        tx.run(query, function_name=f["name"])

class KnowledgeGraphManager(): 
    def __init__(self, uri, user, password, project_name, info_dict):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.project_manager = ProjectManager(self.driver, project_name)
        self.folder_manager = FolderManager(self.driver, info_dict, project_name)
        self.file_manager = FileManager(self.driver, info_dict )
        self.class_function_manager = ClassAndFunctionManager(self.driver, info_dict)
        self.info_dict = info_dict

    def close(self):
        self.driver.close()
    
    def create_graph(self):
        self.project_manager.create_project()
        self.folder_manager.create_folders()
        self.file_manager.create_files()
        self.class_function_manager.create_classes_and_functions()

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
    chem_folder_path = "/data/shared/projects/graphRAG/CDPKit/Doc/Doxygen/Python-API/Source/CDPL/Chem"
    # pharm_folder_path = "/data/shared/projects/graphRAG/CDPKit/Doc/Doxygen/Python-API/Source/CDPL/Pharm"
    all_files_info = DocParser(chem_folder_path).parse_files()
    # all_files_info = DocParser(pharm_folder_path, all_files_info).parse_files()
    cdpkit_graph_manager = KnowledgeGraphManager(uri, username, password, project_name="CDPKit", info_dict=all_files_info)
    cdpkit_graph_manager.clean_database()
    cdpkit_graph_manager.create_graph()
    cdpkit_graph_manager.close()

