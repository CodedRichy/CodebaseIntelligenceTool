from typing import Dict, List, Optional, Tuple
from tree_sitter import Language, Parser, Node
import tree_sitter_python
import tree_sitter_javascript

class CodeElement:
    def __init__(self, name: str, type_: str, file_path: str,
                 start_line: int, end_line: int, content: str = "", **kwargs):
        self.name = name
        self.type = type_
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.content = content  # Raw source code snippet
        self.extra_data = kwargs

class ImportElement:
    def __init__(self, module: str, imported_items: List[str],
                 file_path: str, line: int, import_type: str = 'import'):
        self.module = module
        self.imported_items = imported_items
        self.file_path = file_path
        self.line = line
        self.import_type = import_type  # 'import' or 'from'

class FunctionCall:
    def __init__(self, caller_function: str, called_function: str,
                 file_path: str, line: int):
        self.caller_function = caller_function
        self.called_function = called_function
        self.file_path = file_path
        self.line = line

class ParserService:
    def __init__(self):
        # Initialize tree-sitter parsers
        self.parsers = {}
        self._setup_parsers()

    def _setup_parsers(self):
        """Set up tree-sitter parsers for supported languages."""
        try:
            python_lang = Language(tree_sitter_python.language())
            js_lang = Language(tree_sitter_javascript.language())

            self.parsers['.py'] = Parser(python_lang)
            self.parsers['.js'] = Parser(js_lang)
            self.parsers['.ts'] = Parser(js_lang)

        except Exception as e:
            raise Exception(f"Failed to initialize tree-sitter parsers: {e}")

    def parse_file(self, file_path: str) -> Optional[Dict]:
        """Parse a single file and extract code elements."""
        try:
            with open(file_path, 'rb') as f:
                code = f.read()

            # Determine language from file extension
            _, ext = file_path.rsplit('.', 1) if '.' in file_path else ('', '')
            ext = f'.{ext}'

            if ext not in self.parsers:
                return None

            parser = self.parsers[ext]
            tree = parser.parse(code)

            if ext == '.py':
                return self._parse_python_file(tree.root_node, file_path, code.decode('utf-8', errors='ignore'))
            elif ext in ['.js', '.ts']:
                return self._parse_javascript_file(tree.root_node, file_path, code.decode('utf-8', errors='ignore'))

        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return None

    def _parse_python_file(self, root_node: Node, file_path: str, full_code: str) -> Dict[str, Any]:
        """Parse Python file AST and extract elements."""
        classes = []
        functions = []
        imports = []
        function_calls = []

        def traverse(node: Node, current_function: Optional[str] = None):
            if node.type == 'class_definition':
                class_name = self._extract_python_class_name(node)
                if class_name:
                    classes.append(CodeElement(
                        name=class_name,
                        type_='class',
                        file_path=file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        content=full_code[node.start_byte:node.end_byte]
                    ))

            elif node.type == 'function_definition':
                func_name = self._extract_python_function_name(node)
                if func_name:
                    functions.append(CodeElement(
                        name=func_name,
                        type_='function',
                        file_path=file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        content=full_code[node.start_byte:node.end_byte]
                    ))
                    current_function = func_name

            elif node.type == 'import_statement':
                import_elem = self._extract_python_import(node, file_path)
                if import_elem:
                    imports.append(import_elem)

            elif node.type == 'import_from_statement':
                import_elem = self._extract_python_from_import(node, file_path)
                if import_elem:
                    imports.append(import_elem)

            elif node.type == 'call':
                call = self._extract_python_function_call(node, file_path, current_function)
                if call:
                    function_calls.append(call)

            for child in node.children:
                traverse(child, current_function)

        traverse(root_node)

        return {
            'classes': classes,
            'functions': functions,
            'imports': imports,
            'function_calls': function_calls
        }

    def _parse_javascript_file(self, root_node: Node, file_path: str, full_code: str) -> Dict[str, Any]:
        """Parse JavaScript/TypeScript file AST and extract elements."""
        classes = []
        functions = []
        imports = []
        function_calls = []

        def traverse(node: Node, current_function: Optional[str] = None):
            if node.type == 'class_declaration':
                class_name = self._extract_js_class_name(node)
                if class_name:
                    classes.append(CodeElement(
                        name=class_name,
                        type_='class',
                        file_path=file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        content=full_code[node.start_byte:node.end_byte]
                    ))

            elif node.type in ['function_declaration', 'arrow_function', 'function_expression']:
                func_name = self._extract_js_function_name(node)
                if func_name:
                    functions.append(CodeElement(
                        name=func_name,
                        type_='function',
                        file_path=file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        content=full_code[node.start_byte:node.end_byte]
                    ))
                    current_function = func_name

            elif node.type == 'import_statement':
                import_elem = self._extract_js_import(node, file_path)
                if import_elem:
                    imports.append(import_elem)

            elif node.type == 'call_expression':
                call = self._extract_js_function_call(node, file_path, current_function)
                if call:
                    function_calls.append(call)

            for child in node.children:
                traverse(child, current_function)

        traverse(root_node)

        return {
            'classes': classes,
            'functions': functions,
            'imports': imports,
            'function_calls': function_calls
        }

    # Python extraction methods
    def _extract_python_class_name(self, node: Node) -> Optional[str]:
        for child in node.children:
            if child.type == 'identifier':
                return child.text.decode('utf-8')
        return None

    def _extract_python_function_name(self, node: Node) -> Optional[str]:
        for child in node.children:
            if child.type == 'identifier':
                return child.text.decode('utf-8')
        return None

    def _extract_python_import(self, node: Node, file_path: str) -> Optional[ImportElement]:
        # Extract module names from 'import module' statements
        imported_items = []
        for child in node.children:
            if child.type == 'dotted_name' or child.type == 'identifier':
                imported_items.append(child.text.decode('utf-8'))

        if imported_items:
            return ImportElement(
                module=imported_items[0],
                imported_items=imported_items,
                file_path=file_path,
                line=node.start_point[0] + 1,
                import_type='import'
            )
        return None

    def _extract_python_from_import(self, node: Node, file_path: str) -> Optional[ImportElement]:
        # Extract from 'from module import items' statements
        module = None
        imported_items = []

        for child in node.children:
            if child.type == 'dotted_name':
                module = child.text.decode('utf-8')
            elif child.type == 'import_list':
                for item in child.children:
                    if item.type == 'identifier':
                        imported_items.append(item.text.decode('utf-8'))

        if module and imported_items:
            return ImportElement(
                module=module,
                imported_items=imported_items,
                file_path=file_path,
                line=node.start_point[0] + 1,
                import_type='from'
            )
        return None

    def _extract_python_function_call(self, node: Node, file_path: str,
                                    current_function: Optional[str]) -> Optional[FunctionCall]:
        # Extract function call information
        for child in node.children:
            if child.type == 'identifier':
                called_function = child.text.decode('utf-8')
                if current_function:
                    return FunctionCall(
                        caller_function=current_function,
                        called_function=called_function,
                        file_path=file_path,
                        line=node.start_point[0] + 1
                    )
        return None

    # JavaScript extraction methods
    def _extract_js_class_name(self, node: Node) -> Optional[str]:
        for child in node.children:
            if child.type == 'identifier':
                return child.text.decode('utf-8')
        return None

    def _extract_js_function_name(self, node: Node) -> Optional[str]:
        if node.type == 'function_declaration':
            for child in node.children:
                if child.type == 'identifier':
                    return child.text.decode('utf-8')
        # For arrow functions and expressions, they might not have names
        return None

    def _extract_js_import(self, node: Node, file_path: str) -> Optional[ImportElement]:
        # Simplified import extraction for JavaScript
        module = None
        imported_items = []

        for child in node.children:
            if child.type == 'string':
                module = child.text.decode('utf-8').strip('"\'')

        if module:
            return ImportElement(
                module=module,
                imported_items=imported_items,
                file_path=file_path,
                line=node.start_point[0] + 1,
                import_type='import'
            )
        return None

    def _extract_js_function_call(self, node: Node, file_path: str,
                                current_function: Optional[str]) -> Optional[FunctionCall]:
        # Extract function call information
        for child in node.children:
            if child.type == 'identifier':
                called_function = child.text.decode('utf-8')
                if current_function:
                    return FunctionCall(
                        caller_function=current_function,
                        called_function=called_function,
                        file_path=file_path,
                        line=node.start_point[0] + 1
                    )
        return None
