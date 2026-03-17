from typing import Dict, Any, List, Optional
import re

class QueryClassifier:
    """Classify user queries into different types for appropriate handling."""

    def classify_query(self, query: str) -> Dict[str, Any]:
        """Classify a natural language query into a query type with metadata."""
        query_lower = query.lower().strip()

        # Dependency queries
        if any(word in query_lower for word in ['depend', 'dependency', 'imports', 'uses', 'calls']):
            if 'what files depend on' in query_lower or 'which files depend' in query_lower:
                return {
                    'type': 'dependency_query',
                    'subtype': 'files_depending_on',
                    'target': self._extract_target(query, ['depend on', 'depends on'])
                }
            elif 'what does' in query_lower and 'depend on' in query_lower:
                return {
                    'type': 'dependency_query',
                    'subtype': 'file_dependencies',
                    'target': self._extract_target(query, ['depend on'])
                }

        # Explanation queries
        if any(word in query_lower for word in ['explain', 'how does', 'what is', 'describe', 'how']):
            return {
                'type': 'explanation_query',
                'subtype': 'general_explanation',
                'target': self._extract_target(query, ['explain', 'how does', 'what is'])
            }

        # Impact queries
        if any(word in query_lower for word in ['what happens if', 'impact', 'change', 'modify', 'delete', 'remove']):
            return {
                'type': 'impact_query',
                'subtype': 'change_impact',
                'target': self._extract_target(query, ['change', 'modify', 'delete', 'remove'])
            }

        # Architecture queries
        if any(word in query_lower for word in ['architecture', 'structure', 'overview', 'design', 'system']):
            return {
                'type': 'architecture_query',
                'subtype': 'system_overview'
            }

        # Default to explanation query
        return {
            'type': 'explanation_query',
            'subtype': 'general_explanation',
            'target': query
        }

    def _extract_target(self, query: str, keywords: List[str]) -> Optional[str]:
        """Extract the target entity from a query."""
        query_lower = query.lower()

        for keyword in keywords:
            if keyword in query_lower:
                # Find text after the keyword
                idx = query_lower.find(keyword) + len(keyword)
                remaining = query.strip()[idx:].strip()

                # Extract file names, function names, etc.
                # Look for common patterns
                file_match = re.search(r'(\w+\.py|\w+\.js|\w+\.ts)', remaining)
                if file_match:
                    return file_match.group(1)

                # Look for quoted strings
                quote_match = re.search(r'["\']([^"\']+)["\']', remaining)
                if quote_match:
                    return quote_match.group(1)

                # Take first few words as target
                words = remaining.split()[:3]
                return ' '.join(words)

        return None
