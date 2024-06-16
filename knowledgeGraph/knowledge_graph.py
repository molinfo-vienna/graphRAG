from neo4j import GraphDatabase
from DocParser import DocParser


class KnowledgeGraphManager(): 
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_project(self, project_name):
        with self.driver.session() as session:
            session.execute_write(self._create_project_node, project_name)

    @staticmethod
    def _create_project_node(tx, project_name):
        query = """
        CREATE (p:Project {name: $project_name})
        RETURN p
        """
        result = tx.run(query, project_name=project_name)
        return result.single()

    def create_folders(self, info_dict: dict):
        with self.driver.session() as session:
            session.execute_write(self._create_folder_nodes, info_dict)

    @staticmethod
    def _create_folder_nodes(tx, info_dict: dict):
        for folder in info_dict.keys():
            query = """
            CREATE (f:Folder {name: $folder_name})
            RETURN f
            """
            tx.run(query, folder_name=folder)

    def create_folder_relationships(self, project_name, info_dict):
        with self.driver.session() as session:
            session.execute_write(self._create_folder_relationships, project_name, info_dict)

    @staticmethod
    def _create_folder_relationships(tx, project_name, info_dict):
        for folder in info_dict.keys():
            query = """
            MATCH (p:Project {name: $project_name}), (f:Folder {name: $folder_name})
            CREATE (f)-[:INCLUDED_IN]->(p)
            """
            tx.run(query, project_name=project_name, folder_name=folder)

    def create_files(self, info_dict:dict): 
        with self.driver.session() as session:
            session.execute_write(self._create_file_nodes, info_dict)

    @staticmethod
    def _create_file_nodes(tx, info_dict):
        for nested_dict in info_dict.values():
            for file_name in nested_dict.keys():  # Iterate over each key in the nested dictionary
                query = """
                CREATE (f:File {name: $file_name})
                RETURN f
                """
                tx.run(query, file_name=file_name)

    def create_file_relationships(self, info_dict):
        with self.driver.session() as session:
            session.execute_write(self._create_file_relationships, info_dict)

    @staticmethod
    def _create_file_relationships(tx, info_dict):
        for folder, nested_dict in info_dict.items():
            for file_name in nested_dict.keys():
                query = """
                MATCH (fo:Folder {name: $folder_name}), (fi:File {name: $file_name})
                CREATE (fi)-[:INCLUDED_IN]->(fo)
                """
                tx.run(query, folder_name=folder, file_name=file_name)
    
    def create_graph(self, project_name: str, info_dict: dict):
        # self.create_project(project_name)
        # self.create_folders(info_dict)
        # self.create_folder_relationships (project_name, info_dict)
        # self.create_files(info_dict)
        self.create_file_relationships(info_dict)

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
    pharm_folder_path = "/data/shared/projects/graphRAG/CDPKit/Doc/Doxygen/Python-API/Source/CDPL/Pharm"
    all_files_info = DocParser(chem_folder_path).parse_files()
    all_files_info = DocParser(pharm_folder_path, all_files_info).parse_files()
    all_files_info
    cdpkit_graph_manager = KnowledgeGraphManager(uri, username, password)
    # cdpkit_graph_manager.clean_database()
    cdpkit_graph_manager.create_graph("CDPKit", all_files_info)
    cdpkit_graph_manager.close()

