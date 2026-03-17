import os
from typing import List, Dict, Any
import requests
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import LLMResult
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from graph_builder.graph_builder_service import GraphBuilderService

class GrokLLM(LLM):
    """Custom LLM class for Grok/xAI integration."""

    model_name: str = "grok-beta"
    temperature: float = 0.1
    max_tokens: int = 2048
    api_key: str = ""

    def __init__(self, api_key: str, model_name: str = "grok-beta", temperature: float = 0.1):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature

    @property
    def _llm_type(self) -> str:
        return "grok"

    def _call(self, prompt: str, stop: List[str] = None, run_manager: CallbackManagerForLLMRun = None) -> str:
        """Make API call to Grok."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "messages": [{"role": "user", "content": prompt}],
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False
        }

        if stop:
            data["stop"] = stop

        try:
            response = requests.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Grok API error: {str(e)}")

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

class AIEngine:
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, grok_api_key: str, openai_api_key: str = None):
        self.graph_service = GraphBuilderService(neo4j_uri, neo4j_user, neo4j_password)

        # Use OpenAI for embeddings if key provided
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key) if openai_api_key else None
        if not self.embeddings:
            print("Warning: No OpenAI API key provided. Vector-based search will be disabled.")

        # Use Grok for text generation
        self.llm = GrokLLM(api_key=grok_api_key, model_name="grok-beta", temperature=0.1)

    def build_code_embeddings(self, files: List[Dict]) -> Neo4jVector:
        """Build vector embeddings for code files."""
        documents = []

        for file_info in files:
            try:
                loader = TextLoader(file_info['absolute_path'])
                docs = loader.load()
                documents.extend(docs)
            except Exception as e:
                print(f"Error loading file {file_info['absolute_path']}: {e}")

        # Split documents into chunks
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = text_splitter.split_documents(documents)

        # Create vector store
        vectorstore = Neo4jVector.from_documents(
            split_docs,
            self.embeddings,
            url=os.getenv('NEO4J_URI'),
            username=os.getenv('NEO4J_USER'),
            password=os.getenv('NEO4J_PASSWORD')
        )

        return vectorstore

    def query_codebase_with_context(self, query: str, query_type: Dict[str, Any], vectorstore: Any = None) -> Dict[str, Any]:
        """Query the codebase using natural language and graph context."""
        # Get relevant context from the knowledge graph based on query type
        graph_context = self._get_graph_context(query, query_type)
        
        # Build context string for the prompt
        context_parts = []
        if graph_context.get('files'):
            context_parts.append("Relevant Files:")
            for f in graph_context['files']:
                context_parts.append(f"- {f['path']}")
        
        if graph_context.get('dependencies'):
            context_parts.append("\nCode Relationships:")
            for dep in graph_context['dependencies']:
                context_parts.append(f"- {dep.get('from_file', 'Unknown')} depends on {dep.get('to_file', 'Unknown')} ({dep.get('dependency_type', 'import')})")

        context_str = "\n".join(context_parts)
        
        # Build a robust prompt
        system_prompt = f"""You are an advanced AI codebase assistant. 
Analyze the following context from a code knowledge graph to answer the user's question accurately.

Graph Context:
{context_str}

User Question: {query}

Instructions:
- Be technical and precise.
- Reference specific files and relationships from the context.
- If the context doesn't contain the answer, tell the user what's missing.
- Use a professional SaaS engineer tone."""

        # Get answer from Grok
        answer = self.llm._call(system_prompt)

        return {
            'answer': answer,
            'related_files': [f['path'] for f in graph_context.get('files', []) if 'path' in f],
            'graph_context': graph_context
        }

    def _get_graph_context(self, query: str, query_type: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get relevant context from the knowledge graph."""
        context = {}
        target = query_type.get('target') if query_type else None
        
        # Handle based on query type
        if query_type and query_type['type'] == 'dependency_query':
            if target:
                query_cypher = f"""
                MATCH (f1:File)-[r:IMPORTS|DEPENDS_ON]->(f2:File)
                WHERE f1.path CONTAINS '{target}' OR f2.path CONTAINS '{target}'
                RETURN f1.path as from_file, f2.path as to_file, type(r) as dependency_type
                LIMIT 20
                """
            else:
                query_cypher = """
                MATCH (f1:File)-[r:IMPORTS|DEPENDS_ON]->(f2:File)
                RETURN f1.path as from_file, f2.path as to_file, type(r) as dependency_type
                LIMIT 10
                """
            context['dependencies'] = self.graph_service.query_codebase(query_cypher)

        # General file/class context for explanation or other queries
        if 'auth' in query.lower() or (target and 'auth' in target.lower()):
            query_cypher = """
            MATCH (f:File)-[:DEFINES]->(c:Class)
            WHERE c.name =~ '(?i).*auth.*' OR f.path =~ '(?i).*auth.*'
            RETURN f.path as path, c.name as class_name
            """
            context['files'] = self.graph_service.query_codebase(query_cypher)
        
        if not context.get('files') and target:
            # Search for the target in the graph
            query_cypher = f"""
            MATCH (f:File)
            WHERE f.path CONTAINS '{target}'
            RETURN f.path as path
            """
            context['files'] = self.graph_service.query_codebase(query_cypher)

        return context

    def get_architecture_overview(self, repo_name: str) -> Dict[str, Any]:
        """Get an overview of the repository architecture."""
        # Query for high-level structure
        structure_query = f"""
        MATCH (r:Repository {{name: '{repo_name}'}})-[:CONTAINS]->(f:File)
        RETURN f.extension as language, count(f) as file_count
        ORDER BY file_count DESC
        """

        language_stats = self.graph_service.query_codebase(structure_query)

        # Query for class/function counts
        code_elements_query = f"""
        MATCH (r:Repository {{name: '{repo_name}'}})-[:CONTAINS]->(f:File)-[:DEFINES]->(element)
        RETURN labels(element)[0] as element_type, count(element) as count
        """

        element_counts = self.graph_service.query_codebase(code_elements_query)

        return {
            'language_distribution': language_stats,
            'code_elements': element_counts
        }
