from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from services.repo_ingestion import RepoIngestionService, RepositoryInfo
from parsers.parser_service import ParserService
from parsers.dependency_extractor import DependencyExtractor
from graph_builder.graph_builder_service import GraphBuilderService
import os

# Pydantic models for API requests/responses
class RepoIngestionRequest(BaseModel):
    url: str

class RepoIngestionResponse(BaseModel):
    repo_name: str
    files_count: int
    classes_count: int
    functions_count: int
    message: str

class FileInfo(BaseModel):
    path: str
    extension: str
    size: int

class DependencyInfo(BaseModel):
    file_path: str
    imports: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    function_calls: List[Dict[str, Any]]

class FunctionCallInfo(BaseModel):
    caller: str
    caller_file: str
    callee: str
    callee_file: str
    line: int

# Dependency injection functions
def get_repo_service() -> RepoIngestionService:
    return RepoIngestionService()

def get_parser_service() -> ParserService:
    return ParserService()

def get_dependency_extractor(parser_service: ParserService = Depends(get_parser_service)) -> DependencyExtractor:
    return DependencyExtractor(parser_service)

def get_graph_service() -> GraphBuilderService:
    # Get Neo4j connection details from environment variables
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password')
    return GraphBuilderService(uri, user, password)

# Create router
router = APIRouter()

@router.post("/ingest-repo", response_model=RepoIngestionResponse)
async def ingest_repository(
    request: RepoIngestionRequest,
    repo_service: RepoIngestionService = Depends(get_repo_service),
    parser_service: ParserService = Depends(get_parser_service),
    dependency_extractor: DependencyExtractor = Depends(get_dependency_extractor),
    graph_service: GraphBuilderService = Depends(get_graph_service)
):
    """Ingest a Git repository, parse it, and build the knowledge graph."""
    try:
        # Step 1: Clone and scan repository
        repo_info = await repo_service.clone_repository(request.url)
        repo_info = await repo_service.scan_repository(repo_info)

        # Step 2: Parse all files and extract code elements
        all_classes = []
        all_functions = []

        for file_info in repo_info.files:
            parsed_data = parser_service.parse_file(file_info['absolute_path'])
            if parsed_data:
                all_classes.extend(parsed_data['classes'])
                all_functions.extend(parsed_data['functions'])

        # Step 3: Extract dependencies
        dependencies = dependency_extractor.extract_dependencies(repo_info.files)

        # Step 4: Build relationships
        import_relationships = dependency_extractor.build_import_relationships(
            dependencies['imports'], repo_info.files
        )
        function_call_relationships = dependency_extractor.build_function_call_relationships(
            dependencies['function_calls'], all_functions
        )

        # Step 5: Save to graph database
        repo_id = graph_service.create_repository_node({
            'name': repo_info.name,
            'url': repo_info.url
        })
        graph_service.create_file_nodes(repo_id, repo_info.files)
        graph_service.create_code_element_nodes(all_classes, all_functions)
        graph_service.create_relationships(import_relationships, function_call_relationships)

        # Step 6: Clean up
        await repo_service.cleanup_repository(repo_info)

        return RepoIngestionResponse(
            repo_name=repo_info.name,
            files_count=len(repo_info.files),
            classes_count=len(all_classes),
            functions_count=len(all_functions),
            message="Repository successfully ingested and analyzed"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest repository: {str(e)}")

@router.get("/graph/files", response_model=List[FileInfo])
async def get_files(graph_service: GraphBuilderService = Depends(get_graph_service)):
    """Get all files in the knowledge graph."""
    try:
        files = graph_service.get_files()
        return [FileInfo(**file) for file in files]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve files: {str(e)}")

@router.get("/graph/dependencies", response_model=DependencyInfo)
async def get_file_dependencies(
    file_path: str,
    graph_service: GraphBuilderService = Depends(get_graph_service)
):
    """Get dependencies for a specific file."""
    try:
        dependencies = graph_service.get_file_dependencies(file_path)
        return DependencyInfo(**dependencies)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dependencies: {str(e)}")

@router.get("/graph/calls", response_model=List[FunctionCallInfo])
async def get_function_calls(
    function_name: Optional[str] = None,
    graph_service: GraphBuilderService = Depends(get_graph_service)
):
    """Get function call relationships."""
    try:
        calls = graph_service.get_function_calls(function_name)
        return [FunctionCallInfo(**call) for call in calls]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve function calls: {str(e)}")

@router.delete("/repository/{repo_name}")
async def clear_repository(
    repo_name: str,
    graph_service: GraphBuilderService = Depends(get_graph_service)
):
    """Clear all data for a repository."""
    try:
        graph_service.clear_repository(repo_name)
        return {"message": f"Repository {repo_name} cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear repository: {str(e)}")
