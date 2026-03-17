from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from parsers.parser_service import CodeElement, ImportElement, FunctionCall

class GraphBuilderService:
    def __init__(self, uri: str, user: str, password: str):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Test connection
            self.driver.verify_connectivity()
            self._create_indexes()
        except Exception as e:
            print(f"CRITICAL: Failed to connect to Neo4j: {e}")
            self.driver = None

    def _create_indexes(self):
        """Create necessary indexes for performance."""
        if not self.driver:
            return
        with self.driver.session() as session:
            # Create indexes/constraints with individual try-except to handle conflicts gracefully
            try:
                session.run("CREATE INDEX file_path IF NOT EXISTS FOR (f:File) ON (f.path)")
            except: pass
            
            try:
                session.run("CREATE INDEX function_name IF NOT EXISTS FOR (fn:Function) ON (fn.name)")
            except: pass
            
            try:
                session.run("CREATE INDEX class_name IF NOT EXISTS FOR (c:Class) ON (c.name)")
            except: pass

            try:
                session.run("CREATE CONSTRAINT file_path_unique IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE")
            except: pass

    def close(self):
        """Close the Neo4j driver."""
        self.driver.close()

    def create_repository_node(self, repo_info: Dict) -> str:
        """Create a repository node and return its ID."""
        if not self.driver:
            raise Exception("Database driver not initialized. Check Neo4j connection.")
        with self.driver.session() as session:
            result = session.run(
                """
                MERGE (r:Repository {url: $url})
                ON CREATE SET r.name = $name, r.created_at = datetime()
                RETURN id(r) as repo_id
                """,
                name=repo_info['name'],
                url=repo_info['url']
            )
            record = result.single()
            return record['repo_id']

    def create_file_nodes(self, repo_id: int, files: List[Dict]):
        """Create file nodes and connect them to the repository."""
        if not self.driver:
            return
        with self.driver.session() as session:
            for file_info in files:
                session.run(
                    """
                    MATCH (r:Repository) WHERE id(r) = $repo_id
                    MERGE (f:File {path: $path})
                    ON CREATE SET f.absolute_path = $absolute_path,
                                  f.extension = $extension,
                                  f.size = $size
                    MERGE (r)-[:CONTAINS]->(f)
                    """,
                    repo_id=repo_id,
                    path=file_info['path'],
                    absolute_path=file_info['absolute_path'],
                    extension=file_info['extension'],
                    size=file_info['size']
                )

    def create_code_element_nodes(self, classes: List[CodeElement],
                                functions: List[CodeElement]):
        """Create class and function nodes and connect them to files."""
        if not self.driver:
            return
        with self.driver.session() as session:
            # Create class nodes
            for cls in classes:
                session.run(
                    """
                    MATCH (f:File {path: $file_path})
                    MERGE (c:Class {name: $name, file_path: $file_path})
                    ON CREATE SET c.start_line = $start_line,
                                  c.end_line = $end_line,
                                  c.content = $content
                    MERGE (f)-[:DEFINES]->(c)
                    """,
                    file_path=cls.file_path,
                    name=cls.name,
                    start_line=cls.start_line,
                    end_line=cls.end_line,
                    content=cls.content
                )

            # Create function nodes
            for func in functions:
                session.run(
                    """
                    MATCH (f:File {path: $file_path})
                    MERGE (fn:Function {name: $name, file_path: $file_path})
                    ON CREATE SET fn.start_line = $start_line,
                                  fn.end_line = $end_line,
                                  fn.content = $content
                    MERGE (f)-[:DEFINES]->(fn)
                    """,
                    file_path=func.file_path,
                    name=func.name,
                    start_line=func.start_line,
                    end_line=func.end_line,
                    content=func.content
                )

    def create_relationships(self, import_relationships: List[Dict],
                           function_call_relationships: List[Dict]):
        """Create import and function call relationships."""
        with self.driver.session() as session:
            # Create import relationships
            for rel in import_relationships:
                session.run(
                    """
                    MATCH (f1:File {path: $source_file})
                    MATCH (f2:File {path: $target_file})
                    MERGE (f1)-[r:IMPORTS {module: $module, import_type: $import_type}]->(f2)
                    ON CREATE SET r.line = $line
                    """,
                    source_file=rel['source_file'],
                    target_file=rel['target_file'],
                    module=rel['module'],
                    import_type=rel['import_type'],
                    line=rel['line']
                )

            # Create function call relationships
            for rel in function_call_relationships:
                # Try to match functions first
                session.run(
                    """
                    MATCH (fn1:Function {name: $source_function, file_path: $source_file})
                    MATCH (fn2:Function {name: $target_function, file_path: $target_file})
                    MERGE (fn1)-[r:CALLS]->(fn2)
                    ON CREATE SET r.line = $line
                    """,
                    source_function=rel['source_function'],
                    target_function=rel['target_function'],
                    source_file=rel['source_file'],
                    target_file=rel['target_file'],
                    line=rel['line']
                )

    def get_files(self) -> List[Dict[str, Any]]:
        """Get all files in the graph."""
        if not self.driver:
            return []
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (f:File)
                RETURN f.path as path, f.extension as extension,
                       f.size as size
                ORDER BY f.path
                """
            )
            return [record.data() for record in result]

    def get_file_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Get dependencies for a specific file."""
        with self.driver.session() as session:
            # Get imports
            imports_result = session.run(
                """
                MATCH (f1:File {path: $file_path})-[r:IMPORTS]->(f2:File)
                RETURN f2.path as imported_file, r.module as module,
                       r.import_type as import_type, r.line as line
                """,
                file_path=file_path
            )
            imports = [record.data() for record in imports_result]

            # Get functions defined in this file
            functions_result = session.run(
                """
                MATCH (f:File {path: $file_path})-[:DEFINES]->(fn:Function)
                RETURN fn.name as function_name, fn.start_line as start_line,
                       fn.end_line as end_line
                """,
                file_path=file_path
            )
            functions = [record.data() for record in functions_result]

            # Get function calls from this file
            calls_result = session.run(
                """
                MATCH (fn1:Function {file_path: $file_path})-[r:CALLS]->(fn2:Function)
                RETURN fn1.name as caller, fn2.name as callee,
                       fn2.file_path as callee_file, r.line as line
                """,
                file_path=file_path
            )
            calls = [record.data() for record in calls_result]

            return {
                'file_path': file_path,
                'imports': imports,
                'functions': functions,
                'function_calls': calls
            }

    def get_function_calls(self, function_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get function call relationships."""
        with self.driver.session() as session:
            if function_name:
                result = session.run(
                    """
                    MATCH (fn1:Function)-[r:CALLS]->(fn2:Function {name: $function_name})
                    RETURN fn1.name as caller, fn1.file_path as caller_file,
                           fn2.name as callee, fn2.file_path as callee_file,
                           r.line as line
                    """,
                    function_name=function_name
                )
            else:
                result = session.run(
                    """
                    MATCH (fn1:Function)-[r:CALLS]->(fn2:Function)
                    RETURN fn1.name as caller, fn1.file_path as caller_file,
                           fn2.name as callee, fn2.file_path as callee_file,
                           r.line as line
                    LIMIT 100
                    """
                )

            return [record.data() for record in result]

    def clear_repository(self, repo_name: str):
        """Clear all data for a repository."""
        with self.driver.session() as session:
            session.run(
                """
                MATCH (r:Repository {name: $repo_name})
                DETACH DELETE r
                """,
                repo_name=repo_name
            )
