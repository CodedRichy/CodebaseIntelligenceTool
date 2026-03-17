# Neo4j Graph Database Schema for Codebase Intelligence

# Node Types:
# - Repository: Root node representing a Git repository
# - File: Represents a source code file
# - Class: Represents a class definition
# - Function: Represents a function/method definition

# Relationship Types:
# - CONTAINS: Repository -> File (repository contains files)
# - DEFINES: File -> Class/Function (file defines classes/functions)
# - IMPORTS: File -> File (file imports from another file)
# - CALLS: Function -> Function (function calls another function)

# Indexes for performance
CREATE INDEX repository_name IF NOT EXISTS FOR (r:Repository) ON (r.name);
CREATE INDEX repository_url IF NOT EXISTS FOR (r:Repository) ON (r.url);
CREATE INDEX file_path IF NOT EXISTS FOR (f:File) ON (f.path);
CREATE INDEX class_name IF NOT EXISTS FOR (c:Class) ON (c.name);
CREATE INDEX class_file IF NOT EXISTS FOR (c:Class) ON (c.file_path);
CREATE INDEX function_name IF NOT EXISTS FOR (fn:Function) ON (fn.name);
CREATE INDEX function_file IF NOT EXISTS FOR (fn:Function) ON (fn.file_path);

# Constraints (uniqueness)
CREATE CONSTRAINT repository_url_unique IF NOT EXISTS FOR (r:Repository) REQUIRE r.url IS UNIQUE;
CREATE CONSTRAINT file_path_unique IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE;
CREATE CONSTRAINT class_unique IF NOT EXISTS FOR (c:Class) REQUIRE (c.name, c.file_path) IS UNIQUE;
CREATE CONSTRAINT function_unique IF NOT EXISTS FOR (fn:Function) REQUIRE (fn.name, fn.file_path) IS UNIQUE;
