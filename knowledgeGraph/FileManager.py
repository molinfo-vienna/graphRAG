from neo4j import Driver, Transaction

class FileManager():
    def __init__(self, driver: Driver, info_dict: dict) -> None:
        self.driver = driver 
        self.info_dict = info_dict

    def create_files(self) -> None: 
        with self.driver.session() as session:
            session.execute_write(self._create_file_nodes_and_relationships)

    def _create_file_nodes_and_relationships(self, tx: Transaction) -> None:
         for folder, nested_dict in self.info_dict.items(): # loops through all the files in a folder and creates their nodes and relationships
             for file_name in nested_dict.keys():
                self._create_file_nodes(tx, file_name)
                self._create_file_relationships(tx, folder, file_name)

  
    def _create_file_nodes(self, tx: Transaction, file_name: str) -> None:
        # creates file node if it does not already exist
        query = """
        MERGE (f:File {name: $file_name})
        RETURN f
        """
        tx.run(query, file_name=file_name)

    def _create_file_relationships(self, tx: Transaction, folder: str, file_name: str) -> None:
        # creates relationship from file to folder it is included in (if it does not already exist)
        query = """
        MATCH (fo:Folder {name: $folder_name}), (fi:File {name: $file_name})
        MERGE (fi)-[:INCLUDED_IN]->(fo)
        """
        tx.run(query, folder_name=folder, file_name=file_name)