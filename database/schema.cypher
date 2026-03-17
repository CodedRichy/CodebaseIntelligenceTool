# Database schema for Neo4j graph database
# This file contains Cypher queries to set up the graph schema

# Node labels:
# - Repository: Root node representing a Git repository
# - File: Represents a source code file
# - Class: Represents a class definition
# - Function: Represents a function/method definition
# - Module: Represents a module/package (for languages that support it)

# Relationship types:
# - CONTAINS: Repository -> File (repository contains files)
# - DEFINES: File -> Class/Function (file defines classes/functions)
# - HAS_METHOD: Class -> Function (class has methods)
# - IMPORTS: File -> File (file imports from another file)
# - DEPENDS_ON: File -> File (file depends on another file)
# - CALLS: Function -> Function (function calls another function)

# Indexes for performance
CREATE INDEX repository_name IF NOT EXISTS FOR (r:Repository) ON (r.name);
CREATE INDEX file_path IF NOT EXISTS FOR (f:File) ON (f.path);
CREATE INDEX class_name IF NOT EXISTS FOR (c:Class) ON (c.name);
CREATE INDEX function_name IF NOT EXISTS FOR (fn:Function) ON (fn.name);

# Constraints
CREATE CONSTRAINT repository_url_unique IF NOT EXISTS FOR (r:Repository) REQUIRE r.url IS UNIQUE;
CREATE CONSTRAINT file_path_unique IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE;
