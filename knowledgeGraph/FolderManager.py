from neo4j import Driver, Transaction

class FolderManager():  
    def __init__(self, driver: Driver, info_dict: dict, project_name: str):
        self.driver = driver
        self.info_dict = info_dict
        self.project_name = project_name
        
    def create_folders(self) -> None:
        with self.driver.session() as session:
            session.execute_write(self._create_folder_nodes_and_relationships, self.info_dict, self.project_name)


    def _create_folder_nodes_and_relationships(self, tx: Transaction, info_dict: dict, project_name: str) -> None:
        for folder in info_dict.keys(): # loops through each folder and creates its node and relationships
            self._create_folder_nodes(tx, folder)
            self._create_folder_relationships(tx, project_name, folder)

    def _create_folder_nodes(self, tx: Transaction, folder: str) -> None:
        # creates the folder node if it does not already exist
        query = """
        MERGE (f:Folder {name: $folder_name})
        RETURN f
        """
        tx.run(query, folder_name=folder)

    def _create_folder_relationships(self, tx: Transaction, project_name: str, folder: str) -> None:
        # creates the edge between folder and the project it is included in (if it does not already exist)
        query = """
        MATCH (p:Project {name: $project_name}), (f:Folder {name: $folder_name})
        MERGE (f)-[:INCLUDED_IN]->(p)
        """
        tx.run(query, project_name=project_name, folder_name=folder)