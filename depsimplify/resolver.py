from typing import Dict, List, Set, Tuple, Optional
import requests
from packaging.version import Version, parse
from packaging.specifiers import SpecifierSet
from packaging.requirements import Requirement
from .exceptions import DependencyError
from .cache import DependencyCache

class DependencyResolver:
    """Resolves dependency conflicts and finds compatible versions"""
    
    def __init__(self):
        self.cache = DependencyCache()
        self.pypi_url = "https://pypi.org/pypi/{package}/json"

    def _get_package_metadata(self, package: str) -> dict:
        """Get package metadata from PyPI"""
        try:
            response = requests.get(self.pypi_url.format(package=package))
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as e:
            raise DependencyError(f"Failed to fetch metadata for {package}: {str(e)}")
        
    def _get_package_dependencies(self, package: str, version: str = None) -> Dict[str, List[str]]:
        """Get package dependencies from PyPI"""
        try:
            pkg_data = self._get_package_metadata(package)
            
            # Get dependencies from info section (these are the declared dependencies)
            info = pkg_data.get('info', {})
            requires_dist = info.get('requires_dist', []) or []  # Handle None case
            dependencies = {}
            
            for req_str in requires_dist:
                try:
                    # Skip environment markers and extras
                    if ';' in req_str:
                        req_str = req_str.split(';')[0].strip()
                    if 'extra ==' in req_str:
                        continue
                        
                    req = Requirement(req_str)
                    if req.specifier:
                        dependencies[req.name] = [str(spec) for spec in req.specifier]
                except Exception:
                    continue
                    
            return dependencies
            
        except DependencyError:
            return {}

    def _check_version_compatibility(self, versions: List[str], specs: List[str]) -> Set[str]:
        """Check which versions are compatible with given specifications"""
        compatible = set()
        if not versions or not specs:
            return compatible
            
        try:
            spec_set = SpecifierSet(','.join(specs))
            for version in versions:
                try:
                    if spec_set.contains(version):
                        compatible.add(version)
                except Exception:
                    continue
        except Exception:
            pass
        return compatible

    def find_conflicts(self, dependencies: Dict[str, List[str]]) -> Dict[str, Dict[str, List[str]]]:
        """Find conflicting dependencies"""
        if not dependencies:
            return {}
            
        conflicts = {}
        
        # Check cache first
        cached_conflicts = self.cache.get_conflicts(dependencies)
        if cached_conflicts:
            return cached_conflicts

        try:
            # First pass: Get all direct and transitive dependencies
            dep_graph = {}
            for pkg_name, specs in dependencies.items():
                try:
                    # Get package metadata and check direct compatibility
                    pkg_data = self._get_package_metadata(pkg_name)
                    all_versions = list(pkg_data.get('releases', {}).keys())
                    if not all_versions:
                        conflicts[pkg_name] = {'error': 'No versions available'}
                        continue
                        
                    compatible = self._check_version_compatibility(all_versions, specs)
                    
                    if not compatible:
                        conflicts[pkg_name] = {'direct': specs}
                        continue
                        
                    # Get transitive dependencies
                    trans_deps = self._get_package_dependencies(pkg_name)
                    if trans_deps:  # Only add to graph if there are dependencies
                        dep_graph[pkg_name] = {
                            'specs': specs,
                            'requires': trans_deps
                        }
                    
                except DependencyError as e:
                    conflicts[pkg_name] = {'error': str(e)}
                except Exception as e:
                    conflicts[pkg_name] = {'error': f'Unexpected error: {str(e)}'}

            # Second pass: Check for conflicts between direct and transitive dependencies
            for pkg_name, pkg_info in dep_graph.items():
                for dep_name, dep_specs in pkg_info['requires'].items():
                    if dep_name in dependencies:  # Only check conflicts with direct dependencies
                        try:
                            # Get all versions of the dependency
                            dep_data = self._get_package_metadata(dep_name)
                            all_versions = list(dep_data.get('releases', {}).keys())
                            
                            if not all_versions:
                                if dep_name not in conflicts:
                                    conflicts[dep_name] = {}
                                conflicts[dep_name][pkg_name] = ['No versions available']
                                continue
                            
                            # Check compatibility with direct requirement
                            direct_compatible = self._check_version_compatibility(all_versions, dependencies[dep_name])
                            
                            # Check compatibility with transitive requirement
                            trans_compatible = self._check_version_compatibility(all_versions, dep_specs)
                            
                            # If no overlap in compatible versions, we have a conflict
                            if not direct_compatible.intersection(trans_compatible):
                                if dep_name not in conflicts:
                                    conflicts[dep_name] = {}
                                conflicts[dep_name][pkg_name] = dep_specs
                                
                        except DependencyError as e:
                            if dep_name not in conflicts:
                                conflicts[dep_name] = {}
                            conflicts[dep_name]['error'] = str(e)
                        except Exception as e:
                            if dep_name not in conflicts:
                                conflicts[dep_name] = {}
                            conflicts[dep_name]['error'] = f'Unexpected error: {str(e)}'

            # Cache results
            self.cache.store_conflicts(dependencies, conflicts)
            return conflicts
            
        except Exception as e:
            raise DependencyError(f"Error checking conflicts: {str(e)}")

    def get_compatible_versions(self, package: str, conflict: Dict[str, List[str]]) -> List[str]:
        """Get list of versions compatible with all requirements"""
        if not package or not conflict:
            return []
            
        try:
            # Convert conflict specs to sets for JSON serialization
            json_safe_conflict = {k: list(v) if isinstance(v, (list, set)) else v 
                                for k, v in conflict.items()}
            
            # Check cache first
            cached_versions = self.cache.get_compatible_versions(package, json_safe_conflict)
            if cached_versions:
                return cached_versions

            # Get all versions
            pkg_data = self._get_package_metadata(package)
            all_versions = list(pkg_data.get('releases', {}).keys())
            if not all_versions:
                return []

            # Collect all specs
            specs = []
            for spec_list in conflict.values():
                if isinstance(spec_list, (list, set)):
                    specs.extend(spec_list)

            # Find compatible versions
            compatible = self._check_version_compatibility(all_versions, specs)
            if not compatible:
                return []
            
            # Sort and limit results
            compatible_versions = sorted(list(compatible), key=parse, reverse=True)[:5]

            # Cache results
            self.cache.store_compatible_versions(package, json_safe_conflict, compatible_versions)
            return compatible_versions
            
        except DependencyError as e:
            return []  # Return empty list instead of raising error for better UX
        except Exception as e:
            return []
