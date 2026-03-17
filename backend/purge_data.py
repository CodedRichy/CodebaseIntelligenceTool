
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD', 'neo4j')

print(f"Purging Neo4j at {uri}...")

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        # Purge all nodes and relationships
        result = session.run("MATCH (n) DETACH DELETE n")
        summary = result.consume()
        print(f"Purge complete. Nodes deleted: {summary.counters.nodes_deleted}")
    driver.close()
except Exception as e:
    print(f"Purge failed: {e}")
