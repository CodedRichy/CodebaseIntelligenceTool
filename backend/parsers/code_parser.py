import os
from typing import Dict, List, Optional
from tree_sitter import Language, Parser
import tree_sitter_python
import tree_sitter_javascript

class CodeParser:
    def __init__(self):
        # Build language library (this would be done once)
        # For MVP, we'll support Python and JavaScript
        self.languages = {
            'python': Language(tree_sitter_python.language()),
            'javascript': Language(tree_sitter_javascript.language())
        }
        self.parsers = {lang: Parser() for lang in self.languages}
        for lang, parser in self.parsers.items():
            parser.set_language(self.languages[lang])

    def parse_file(self, file_path: str) -> Optional[Dict]:
        """Parse a single file and extract code elements."""
        if not os.path.exists(file_path):
            return None

        # Determine language from file extension
        _, ext = os.path.splitext(file_path)
        language = self._get_language_from_extension(ext)
        if not language or language not in self.parsers:
            return None

        with open(file_path, 'rb') as f:
            code = f.read()

        parser = self.parsers[language]
        tree = parser.parse(code)

        # Extract elements based on language
        if language == 'python':
            return self._extract_python_elements(tree, file_path)
        elif language == 'javascript':
            return self._extract_javascript_elements(tree, file_path)

        return None

    def _get_language_from_extension(self, extension: str) -> Optional[str]:
        """Map file extension to language."""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'javascript'  # For simplicity, treat TypeScript as JavaScript
        }
        return ext_map.get(extension.lower())

    def _extract_python_elements(self, tree, file_path: str) -> Dict:
        """Extract classes, functions, and imports from Python AST."""
        classes = []
        functions = []
        imports = []

        def traverse(node):
            if node.type == 'class_definition':
                class_name = None
                for child in node.children:
                    if child.type == 'identifier':
                        class_name = child.text.decode('utf-8')
                        break
                if class_name:
                    classes.append({
                        'name': class_name,
                        'file_path': os.path.basename(file_path),
                        'line_start': node.start_point[0] + 1,
                        'line_end': node.end_point[0] + 1
                    })

            elif node.type == 'function_definition':
                func_name = None
                for child in node.children:
                    if child.type == 'identifier':
                        func_name = child.text.decode('utf-8')
                        break
                if func_name:
                    functions.append({
                        'name': func_name,
                        'file_path': os.path.basename(file_path),
                        'line_start': node.start_point[0] + 1,
                        'line_end': node.end_point[0] + 1
                    })

            elif node.type == 'import_statement' or node.type == 'import_from_statement':
                # Basic import extraction
                import_text = node.text.decode('utf-8').strip()
                imports.append({
                    'statement': import_text,
                    'file_path': os.path.basename(file_path),
                    'line': node.start_point[0] + 1
                })

            for child in node.children:
                traverse(child)

        traverse(tree.root_node)

        return {
            'classes': classes,
            'functions': functions,
            'imports': imports
        }

    def _extract_javascript_elements(self, tree, file_path: str) -> Dict:
        """Extract classes, functions, and imports from JavaScript AST."""
        classes = []
        functions = []
        imports = []

        def traverse(node):
            if node.type == 'class_declaration':
                class_name = None
                for child in node.children:
                    if child.type == 'identifier':
                        class_name = child.text.decode('utf-8')
                        break
                if class_name:
                    classes.append({
                        'name': class_name,
                        'file_path': os.path.basename(file_path),
                        'line_start': node.start_point[0] + 1,
                        'line_end': node.end_point[0] + 1
                    })

            elif node.type in ['function_declaration', 'arrow_function', 'function_expression']:
                func_name = None
                if node.type == 'function_declaration':
                    for child in node.children:
                        if child.type == 'identifier':
                            func_name = child.text.decode('utf-8')
                            break
                # For arrow functions and expressions, we might not have names
                if func_name:
                    functions.append({
                        'name': func_name,
                        'file_path': os.path.basename(file_path),
                        'line_start': node.start_point[0] + 1,
                        'line_end': node.end_point[0] + 1
                    })

            elif node.type == 'import_statement':
                import_text = node.text.decode('utf-8').strip()
                imports.append({
                    'statement': import_text,
                    'file_path': os.path.basename(file_path),
                    'line': node.start_point[0] + 1
                })

            for child in node.children:
                traverse(child)

        traverse(tree.root_node)

        return {
            'classes': classes,
            'functions': functions,
            'imports': imports
        }
