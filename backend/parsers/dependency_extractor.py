from typing import Dict, List, Set, Optional
from parsers.parser_service import ParserService, ImportElement, FunctionCall

class DependencyExtractor:
    def __init__(self, parser_service: ParserService):
        self.parser_service = parser_service

    def extract_dependencies(self, files: List[Dict]) -> Dict[str, Dict]:
        """Extract all dependencies from a list of files."""
        all_imports = []
        all_function_calls = []

        for file_info in files:
            parsed_data = self.parser_service.parse_file(file_info['absolute_path'])
            if parsed_data:
                all_imports.extend(parsed_data['imports'])
                all_function_calls.extend(parsed_data['function_calls'])

        return {
            'imports': all_imports,
            'function_calls': all_function_calls
        }

    def build_import_relationships(self, imports: List[ImportElement],
                                 files: List[Dict]) -> List[Dict]:
        """Build file-to-file import relationships."""
        relationships = []
        file_map = {f['path']: f for f in files}

        for imp in imports:
            # Find the file that provides the imported module
            target_file = self._resolve_import_to_file(imp, files)
            if target_file:
                relationships.append({
                    'source_file': imp.file_path,
                    'target_file': target_file['path'],
                    'relationship_type': 'IMPORTS',
                    'import_type': imp.import_type,
                    'module': imp.module,
                    'line': imp.line
                })

        return relationships

    def build_function_call_relationships(self, function_calls: List[FunctionCall],
                                        functions: List) -> List[Dict]:
        """Build function-to-function call relationships."""
        relationships = []
        function_map = {}

        # Build function lookup map
        for func in functions:
            key = f"{func.file_path}:{func.name}"
            function_map[key] = func

        for call in function_calls:
            # Try to resolve the called function
            caller_key = f"{call.file_path}:{call.caller_function}"
            called_key = f"{call.file_path}:{call.called_function}"

            # First check if it's a call within the same file
            if called_key in function_map:
                relationships.append({
                    'source_function': call.caller_function,
                    'target_function': call.called_function,
                    'source_file': call.file_path,
                    'target_file': call.file_path,
                    'relationship_type': 'CALLS',
                    'line': call.line
                })
            else:
                # Check other files for the called function
                for key, func in function_map.items():
                    if func.name == call.called_function:
                        relationships.append({
                            'source_function': call.caller_function,
                            'target_function': call.called_function,
                            'source_file': call.file_path,
                            'target_file': func.file_path,
                            'relationship_type': 'CALLS',
                            'line': call.line
                        })
                        break

        return relationships

    def _resolve_import_to_file(self, imp: ImportElement, files: List[Dict]) -> Optional[Dict]:
        """Resolve an import statement to the actual file it imports from."""
        # This is a simplified resolver - in practice, this would need
        # much more sophisticated logic to handle relative imports,
        # package structures, etc.

        module = imp.module

        # Handle relative imports (starting with .)
        if module.startswith('.'):
            # For now, skip relative imports as they're complex to resolve
            return None

        # Look for files that match the module name
        for file_info in files:
            # Remove extension and check if it matches
            file_base = file_info['path'].rsplit('.', 1)[0]

            # Direct match
            if file_base == module or file_base.endswith(f'/{module}'):
                return file_info

            # Check if it's a module within a package
            if '/' in file_base:
                parts = file_base.split('/')
                if module in parts:
                    return file_info

        return None
