from neo4j import GraphDatabase, Transaction
from DocParser import DocParser
from ProjectManager import ProjectManager
from FolderManager import FolderManager
from FileManager import FileManager
from ClassManager import ClassManager
from FunctionManager import FunctionManager
import os


class KnowledgeGraphManager(): 
    # responsible for calling the submanagers
    def __init__(self, uri: str, user: str, password: str, project_name: str, info_dict: dict):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.project_manager = ProjectManager(self.driver, project_name)    # handles project nodes and edges 
        self.folder_manager = FolderManager(self.driver, info_dict, project_name)   # handles folder nodes and edges
        self.file_manager = FileManager(self.driver, info_dict )    # handles file nodes and edges
        self.class_manager = ClassManager(self.driver, info_dict)   # handles class nodes and edges
        self.function_manager = FunctionManager(self.driver, info_dict) # handles function nodes and edges 
        self.info_dict = info_dict  # dict from DocParser

    def close(self) -> None:
        self.driver.close()
    
    def create_graph(self) -> None:
        # workflow to create entire knowledge graph
        self.project_manager.create_project()
        self.folder_manager.create_folders()
        self.file_manager.create_files()
        self.class_manager.create_classes()
        self.function_manager.create_functions()

    def clean_database(self) -> None:
        # removes all nodes and edges from the graph database
        with self.driver.session() as session:
            session.execute_write(self._clean_database)

    @staticmethod
    def _clean_database(tx: Transaction) -> None:
        # tx is the transaction object passed from the database session
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        tx.run(query)


if __name__ == "__main__":
    uri = os.getenv("NEO4j_URI")
    username = os.getenv("NEO4j_USER") 
    password = os.getenv("NEO4j_PASSWORD")
    root_path = os.getenv("CDPKit_PATH")
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
        all_files_info = DocParser(folder).parse_dir()
        cdpkit_graph_manager = KnowledgeGraphManager(uri, username, password, project_name="CDPKit", info_dict=all_files_info)
        cdpkit_graph_manager.create_graph()
        cdpkit_graph_manager.close()

