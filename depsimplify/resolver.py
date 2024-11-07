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
        if not package:
            raise DependencyError("Package name cannot be empty")
            
        try:
            response = requests.get(self.pypi_url.format(package=package))
            response.raise_for_status()
            data = response.json()
            if not data or not isinstance(data, dict):
                raise DependencyError(f"No metadata found for package: {package}")
            return data
        except requests.RequestException as e:
            raise DependencyError(f"Failed to fetch metadata for {package}: {str(e)}")
        except ValueError as e:
            raise DependencyError(f"Invalid metadata for {package}: {str(e)}")
        
    def _get_package_dependencies(self, package: str, version: Optional[str] = None) -> Dict[str, List[str]]:
        """Get package dependencies from PyPI"""
        if not package:
            return {}
            
        try:
            pkg_data = self._get_package_metadata(package)
            if not pkg_data or not isinstance(pkg_data, dict):
                return {}
            
            # Get dependencies from info section
            info = pkg_data.get('info', {})
            if not info or not isinstance(info, dict):
                return {}
                
            requires_dist = info.get('requires_dist', [])
            if requires_dist is None:
                requires_dist = []
                
            if not isinstance(requires_dist, list):
                return {}
                
            dependencies = {}
            
            for req_str in requires_dist:
                if not req_str or not isinstance(req_str, str):
                    continue
                try:
                    # Skip environment markers and extras
                    if ';' in req_str:
                        req_str = req_str.split(';')[0].strip()
                    if not req_str or 'extra ==' in req_str:
                        continue
                        
                    req = Requirement(req_str)
                    if req.specifier:
                        dependencies[req.name] = [str(spec) for spec in req.specifier]
                except Exception:
                    continue
                    
            return dependencies
            
        except DependencyError:
            return {}
        except Exception:
            return {}

    def _check_version_compatibility(self, versions: List[str], specs: List[str]) -> Set[str]:
        """Check which versions are compatible with given specifications"""
        compatible = set()
        if not versions or not specs or not isinstance(versions, list) or not isinstance(specs, list):
            return compatible
            
        try:
            spec_set = SpecifierSet(','.join(specs))
            for version in versions:
                if not version or not isinstance(version, str):
                    continue
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
        if not dependencies or not isinstance(dependencies, dict):
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
                if not pkg_name or not specs or not isinstance(specs, list):
                    continue
                    
                try:
                    # Get package metadata and check direct compatibility
                    pkg_data = self._get_package_metadata(pkg_name)
                    if not pkg_data or not isinstance(pkg_data, dict):
                        conflicts[pkg_name] = {'error': 'Failed to fetch package data'}
                        continue
                        
                    releases = pkg_data.get('releases', {})
                    if not releases or not isinstance(releases, dict):
                        conflicts[pkg_name] = {'error': 'No releases available'}
                        continue
                        
                    all_versions = list(releases.keys())
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
            if dep_graph:  # Only proceed if we have dependencies to check
                for pkg_name, pkg_info in dep_graph.items():
                    if not pkg_name or not isinstance(pkg_info, dict):
                        continue
                        
                    pkg_requires = pkg_info.get('requires', {})
                    if not pkg_requires or not isinstance(pkg_requires, dict):
                        continue
                        
                    for dep_name, dep_specs in pkg_requires.items():
                        if not dep_name or not dep_specs or not isinstance(dep_specs, list):
                            continue
                            
                        if dep_name in dependencies:  # Only check conflicts with direct dependencies
                            try:
                                # Check compatibility with direct requirement
                                direct_specs = dependencies.get(dep_name)
                                if not direct_specs or not isinstance(direct_specs, list):
                                    continue

                                # Get all versions of the dependency
                                dep_data = self._get_package_metadata(dep_name)
                                if not dep_data or not isinstance(dep_data, dict):
                                    if dep_name not in conflicts:
                                        conflicts[dep_name] = {}
                                    conflicts[dep_name][pkg_name] = ['Failed to fetch package data']
                                    continue
                                    
                                releases = dep_data.get('releases', {})
                                if not releases or not isinstance(releases, dict):
                                    if dep_name not in conflicts:
                                        conflicts[dep_name] = {}
                                    conflicts[dep_name][pkg_name] = ['No releases available']
                                    continue
                                    
                                all_versions = list(releases.keys())
                                if not all_versions:
                                    if dep_name not in conflicts:
                                        conflicts[dep_name] = {}
                                    conflicts[dep_name][pkg_name] = ['No versions available']
                                    continue
                                
                                # Check compatibility with direct requirement
                                direct_compatible = self._check_version_compatibility(all_versions, direct_specs)
                                
                                # Check compatibility with transitive requirement
                                trans_compatible = self._check_version_compatibility(all_versions, dep_specs)
                                
                                # If no overlap in compatible versions, we have a conflict
                                if not direct_compatible or not trans_compatible or not direct_compatible.intersection(trans_compatible):
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
            if conflicts:
                self.cache.store_conflicts(dependencies, conflicts)
            return conflicts
            
        except Exception as e:
            raise DependencyError(f"Error checking conflicts: {str(e)}")

    def get_compatible_versions(self, package: str, conflict: Dict[str, List[str]]) -> List[str]:
        """Get list of versions compatible with all requirements"""
        if not package:
            raise DependencyError("Package name cannot be empty")
            
        if not conflict or not isinstance(conflict, dict):
            raise DependencyError("Invalid conflict data")
            
        try:
            # Convert conflict specs to sets for JSON serialization
            json_safe_conflict = {k: list(v) if isinstance(v, (list, set)) else v 
                                for k, v in conflict.items() if k and v}
            
            # Check cache first
            cached_versions = self.cache.get_compatible_versions(package, json_safe_conflict)
            if cached_versions:
                return cached_versions

            # Get all versions
            pkg_data = self._get_package_metadata(package)  # This will raise DependencyError for invalid packages
            if not pkg_data or not isinstance(pkg_data, dict):
                raise DependencyError(f"Invalid metadata format for package: {package}")
                
            releases = pkg_data.get('releases', {})
            if not releases or not isinstance(releases, dict):
                raise DependencyError(f"No releases found for package: {package}")
                
            all_versions = list(releases.keys())
            if not all_versions:
                raise DependencyError(f"No versions available for package: {package}")

            # Collect all specs
            specs = []
            for spec_list in conflict.values():
                if isinstance(spec_list, (list, set)):
                    specs.extend(spec for spec in spec_list if spec)
                    
            if not specs:
                raise DependencyError("No valid version specifications found in conflict data")

            # Find compatible versions
            compatible = self._check_version_compatibility(all_versions, specs)
            if not compatible:
                return []
            
            # Sort and limit results
            compatible_versions = sorted(list(compatible), key=parse, reverse=True)[:5]

            # Cache results
            if compatible_versions:
                self.cache.store_compatible_versions(package, json_safe_conflict, compatible_versions)
            return compatible_versions
            
        except DependencyError as e:
            raise
        except Exception as e:
            raise DependencyError(f"Unexpected error: {str(e)}")
