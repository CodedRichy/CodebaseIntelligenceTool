from typing import Dict, List, Any
from neo4j import GraphDatabase
from parsers.code_parser import CodeParser

class GraphBuilderService:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.code_parser = CodeParser()

    def close(self):
        """Close the Neo4j driver."""
        self.driver.close()

    def create_repository_node(self, repo_info: Dict) -> str:
        """Create a repository node and return its ID."""
        with self.driver.session() as session:
            result = session.run(
                """
                CREATE (r:Repository {
                    name: $name,
                    url: $url,
                    created_at: datetime()
                })
                RETURN id(r) as repo_id
                """,
                name=repo_info['name'],
                url=repo_info['url']
            )
            record = result.single()
            return record['repo_id']

    def create_file_nodes(self, repo_id: int, files: List[Dict]):
        """Create file nodes and connect them to the repository."""
        with self.driver.session() as session:
            for file_info in files:
                session.run(
                    """
                    MATCH (r:Repository) WHERE id(r) = $repo_id
                    CREATE (f:File {
                        path: $path,
                        absolute_path: $absolute_path,
                        extension: $extension,
                        size: $size
                    })
                    CREATE (r)-[:CONTAINS]->(f)
                    """,
                    repo_id=repo_id,
                    path=file_info['path'],
                    absolute_path=file_info['absolute_path'],
                    extension=file_info['extension'],
                    size=file_info['size']
                )

    def create_code_elements(self, repo_id: int, files: List[Dict]):
        """Parse files and create code element nodes (classes, functions)."""
        for file_info in files:
            elements = self.code_parser.parse_file(file_info['absolute_path'])
            if not elements:
                continue

            with self.driver.session() as session:
                # Create class nodes
                for cls in elements.get('classes', []):
                    session.run(
                        """
                        MATCH (f:File {path: $file_path})
                        CREATE (c:Class {
                            name: $name,
                            line_start: $line_start,
                            line_end: $line_end
                        })
                        CREATE (f)-[:DEFINES]->(c)
                        """,
                        file_path=file_info['path'],
                        name=cls['name'],
                        line_start=cls['line_start'],
                        line_end=cls['line_end']
                    )

                # Create function nodes
                for func in elements.get('functions', []):
                    session.run(
                        """
                        MATCH (f:File {path: $file_path})
                        CREATE (fn:Function {
                            name: $name,
                            line_start: $line_start,
                            line_end: $line_end
                        })
                        CREATE (f)-[:DEFINES]->(fn)
                        """,
                        file_path=file_info['path'],
                        name=func['name'],
                        line_start=func['line_start'],
                        line_end=func['line_end']
                    )

                # Create import relationships
                for imp in elements.get('imports', []):
                    # This is a simplified approach - in practice, you'd need
                    # to resolve import paths to actual files
                    session.run(
                        """
                        MATCH (f:File {path: $file_path})
                        CREATE (i:Import {
                            statement: $statement,
                            line: $line
                        })
                        CREATE (f)-[:HAS_IMPORT]->(i)
                        """,
                        file_path=file_info['path'],
                        statement=imp['statement'],
                        line=imp['line']
                    )

    def create_dependency_relationships(self, repo_id: int, files: List[Dict]):
        """Analyze files to create dependency relationships."""
        # This is a simplified dependency analysis
        # In a full implementation, you'd use static analysis tools
        # like mypy, eslint, etc. for each language

        with self.driver.session() as session:
            # Example: Python import analysis
            for file_info in files:
                if file_info['extension'] == '.py':
                    try:
                        with open(file_info['absolute_path'], 'r') as f:
                            content = f.read()

                        # Find import statements and create relationships
                        import_lines = [line.strip() for line in content.split('\n')
                                      if line.strip().startswith(('import ', 'from '))]

                        for import_line in import_lines:
                            # This is very basic - real implementation would be much more sophisticated
                            if 'import ' in import_line:
                                # Handle 'import module' or 'from module import ...'
                                if import_line.startswith('from '):
                                    module = import_line.split(' ')[1]
                                else:
                                    module = import_line.split(' ')[1].split('.')[0]

                                # Try to find a file that matches this module
                                session.run(
                                    """
                                    MATCH (f1:File {path: $from_file})
                                    MATCH (f2:File)
                                    WHERE f2.path CONTAINS $module_name
                                    CREATE (f1)-[:DEPENDS_ON {type: 'import'}]->(f2)
                                    """,
                                    from_file=file_info['path'],
                                    module_name=module
                                )
                    except Exception as e:
                        print(f"Error analyzing dependencies for {file_info['path']}: {e}")

    def query_codebase(self, cypher_query: str) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        with self.driver.session() as session:
            result = session.run(cypher_query)
            return [record.data() for record in result]

    def get_repository_overview(self, repo_name: str) -> Dict[str, Any]:
        """Get an overview of a repository."""
        with self.driver.session() as session:
            # Get file count
            file_count_result = session.run(
                """
                MATCH (r:Repository {name: $name})-[:CONTAINS]->(f:File)
                RETURN count(f) as file_count
                """,
                name=repo_name
            )
            file_count = file_count_result.single()['file_count']

            # Get class count
            class_count_result = session.run(
                """
                MATCH (r:Repository {name: $name})-[:CONTAINS]->(f:File)-[:DEFINES]->(c:Class)
                RETURN count(c) as class_count
                """,
                name=repo_name
            )
            class_count = class_count_result.single()['class_count']

            # Get function count
            function_count_result = session.run(
                """
                MATCH (r:Repository {name: $name})-[:CONTAINS]->(f:File)-[:DEFINES]->(fn:Function)
                RETURN count(fn) as function_count
                """,
                name=repo_name
            )
            function_count = function_count_result.single()['function_count']

            return {
                'file_count': file_count,
                'class_count': class_count,
                'function_count': function_count
            }
