
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')

passwords = ['neo4j', 'password', 'admin', '12345678']

for pwd in passwords:
    print(f"Trying {user}:{pwd}...")
    try:
        driver = GraphDatabase.driver(uri, auth=(user, pwd))
        with driver.session() as session:
            result = session.run("RETURN 1 as n")
            record = result.single()
            print(f"Connection successful with password: {pwd}")
            driver.close()
            break
    except Exception as e:
        print(f"Failed with {pwd}: {e}")
