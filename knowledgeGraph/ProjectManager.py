from neo4j import Driver, Transaction

class ProjectManager(): 
    def __init__(self, driver: Driver, project_name: str) -> None:
        self.project_name = project_name
        self.driver = driver
    
    def create_project(self) -> None:
        with self.driver.session() as session:
            session.execute_write(self._create_project_node, self.project_name)

    def _create_project_node(self, tx: Transaction, project_name: str) -> None:
        # Creates the project node if it does not already exist
        query = """
        MERGE (p:Project {name: $project_name})
        RETURN p
        """
        tx.run(query, project_name=project_name)
        

