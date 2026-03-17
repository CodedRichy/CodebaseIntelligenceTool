import os
from typing import List, Dict, Any
import requests
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema import LLMResult
from langchain.chains import RetrievalQA
from langchain.vectorstores import Neo4jVector
from langchain.embeddings import OpenAIEmbeddings  # Keep for embeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader
from graph_builder.graph_service import GraphBuilderService

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

        # Use OpenAI for embeddings (more reliable for code)
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key) if openai_api_key else None

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

    def query_codebase(self, query: str, vectorstore: Neo4jVector) -> Dict[str, Any]:
        """Query the codebase using natural language."""
        # Create retrieval QA chain
        qa_chain = RetrievalQA.from_chain_type(
            self.llm,
            retriever=vectorstore.as_retriever(),
            return_source_documents=True
        )

        # Execute query
        result = qa_chain({"query": query})

        # Enhance with graph-based analysis
        graph_context = self._get_graph_context(query)

        return {
            'answer': result['result'],
            'sources': [doc.page_content for doc in result['source_documents']],
            'graph_context': graph_context
        }

    def _get_graph_context(self, query: str) -> Dict[str, Any]:
        """Get relevant context from the knowledge graph."""
        context = {}

        # Example: Find files related to authentication
        if 'authentication' in query.lower():
            query_cypher = """
            MATCH (f:File)-[:DEFINES]->(c:Class)
            WHERE c.name =~ '(?i).*auth.*'
            RETURN f.path as file_path, c.name as class_name
            """
            auth_classes = self.graph_service.query_codebase(query_cypher)
            context['authentication_classes'] = auth_classes

        # Example: Find dependencies
        elif 'depend' in query.lower():
            query_cypher = """
            MATCH (f1:File)-[r:DEPENDS_ON]->(f2:File)
            RETURN f1.path as from_file, f2.path as to_file, r.type as dependency_type
            LIMIT 10
            """
            dependencies = self.graph_service.query_codebase(query_cypher)
            context['dependencies'] = dependencies

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
