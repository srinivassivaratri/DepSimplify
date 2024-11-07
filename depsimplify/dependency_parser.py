import re
import ast
from typing import Dict, List, Optional
from packaging.requirements import Requirement
from packaging.version import Version, parse
from .exceptions import DependencyError
import os

class DependencyParser:
    """Parser for Python project dependencies"""
    
    def __init__(self):
        self.requirement_pattern = re.compile(r'^([a-zA-Z0-9-_.]+)([<>=!~]+)([a-zA-Z0-9-_.]+)')

    def parse_project_dependencies(self) -> Dict[str, List[str]]:
        """Parse dependencies from requirements.txt and setup.py"""
        deps = {}
        
        # Try requirements.txt first
        try:
            with open('requirements.txt', 'r') as f:
                deps.update(self._parse_requirements(f.readlines()))
        except FileNotFoundError:
            pass
            
        # Try setup.py if it exists
        try:
            with open('setup.py', 'r') as f:
                deps.update(self._parse_setup_py(f.read()))
        except FileNotFoundError:
            pass
            
        if not deps:
            raise DependencyError("No dependencies found in requirements.txt or setup.py")
            
        return deps

    def _parse_requirements(self, lines: List[str]) -> Dict[str, List[str]]:
        """Parse requirements.txt format"""
        deps = {}
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    req = Requirement(line)
                    deps[req.name] = [str(spec) for spec in req.specifier]
                except Exception:
                    continue
        return deps

    def _parse_setup_py(self, content: str) -> Dict[str, List[str]]:
        """Parse setup.py format"""
        deps = {}
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'setup':
                    for keyword in node.keywords:
                        if keyword.arg == 'install_requires' and isinstance(keyword.value, ast.List):
                            for elt in keyword.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    try:
                                        req = Requirement(elt.value)
                                        deps[req.name] = [str(spec) for spec in req.specifier]
                                    except Exception:
                                        continue
        except Exception as e:
            pass
        return deps

    def update_requirements(self, resolved_deps: Dict[str, str], requirements_path: str = 'requirements.txt') -> None:
        """Update requirements.txt with resolved dependencies"""
        try:
            if not os.path.exists(requirements_path):
                raise DependencyError(f"Requirements file not found: {requirements_path}")
                
            with open(requirements_path, 'r') as f:
                lines = f.readlines()
                
            updated_lines = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    updated_lines.append(line)
                    continue
                    
                try:
                    req = Requirement(line)
                    if req.name in resolved_deps:
                        updated_lines.append(f"{req.name}=={resolved_deps[req.name]}")
                    else:
                        updated_lines.append(line)
                except Exception:
                    updated_lines.append(line)
                    
            with open(requirements_path, 'w') as f:
                f.write('\n'.join(updated_lines) + '\n')
                
        except Exception as e:
            raise DependencyError(f"Failed to update requirements.txt: {str(e)}")
