from neo4j import GraphDatabase

'''
def create_graph(tx):
    # Create nodes with labels
    tx.run("CREATE (a:Class {name: 'Tautomer'})")
    tx.run("CREATE (b:Function {name: 'create'})")
    
    # Create relationship
    tx.run("MATCH (a:Class {name: 'Tautomer'}), (b:Function {name: 'create'}) "
           "CREATE (a)-[:HAS]->(b)")
    
def get_people():
    result = tx.run("MATCH (p:Function) RETURN p.name AS name")
    return [(record["name"]) for record in result]


def main(mode:str):
    if mode == "write": 
        with driver.session() as session:
            session.execute_write(create_graph)
    if mode == "read": 
        with driver.session() as session:
            functions = session.execute_read(get_people)
            print(functions)  # Output the list of people in the graph
'''

if __name__ == "__main__":
    uri = "neo4j+s://92611c46.databases.neo4j.io"  
    username = "neo4j"  
    password = "TkKpzBg85DBE3xtJDzKlA-J8s-g-vLkMknVN6hcc_ew"  
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.close()

