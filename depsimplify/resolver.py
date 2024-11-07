from typing import Dict, List, Set
import requests
from packaging.version import Version, parse
from packaging.specifiers import SpecifierSet
from .exceptions import DependencyError
from .cache import DependencyCache

class DependencyResolver:
    """Resolves dependency conflicts and finds compatible versions"""
    
    def __init__(self):
        self.cache = DependencyCache()
        self.pypi_url = "https://pypi.org/pypi/{package}/json"

    def find_conflicts(self, dependencies: Dict[str, List[str]]) -> Dict[str, Dict[str, list]]:
        """Find conflicting dependencies"""
        conflicts = {}
        
        # Check cache first
        cached_conflicts = self.cache.get_conflicts(dependencies)
        if cached_conflicts:
            return cached_conflicts

        # First check direct requirements compatibility
        for pkg_name, pkg_specs in dependencies.items():
            try:
                response = requests.get(self.pypi_url.format(package=pkg_name))
                response.raise_for_status()
                pkg_data = response.json()
                
                # Get all versions for this package
                pkg_versions = self._get_package_versions(pkg_name)
                pkg_spec_set = SpecifierSet(','.join(pkg_specs))
                
                # Find versions that satisfy direct requirements
                compatible_versions = [str(v) for v in pkg_versions if pkg_spec_set.contains(v)]
                
                if not compatible_versions:
                    if pkg_name not in conflicts:
                        conflicts[pkg_name] = {}
                    conflicts[pkg_name]['direct'] = list(pkg_specs)
                    continue

                # Get the latest compatible version to check its dependencies
                latest_compatible = max(compatible_versions, key=parse)
                release_data = [r for r in pkg_data['releases'][latest_compatible] if r.get('requires_dist')]
                
                if release_data:
                    # Check package's dependencies
                    for req in release_data[0].get('requires_dist', []):
                        try:
                            dep_name = req.split(' ')[0].lower()
                            if dep_name in dependencies:
                                dep_specs = req.split('(')[1].split(')')[0] if '(' in req else ''
                                if dep_specs:
                                    # Get the version range required by this package
                                    pkg_dep_spec_set = SpecifierSet(dep_specs)
                                    # Get the version range from direct requirements
                                    direct_spec_set = SpecifierSet(','.join(dependencies[dep_name]))
                                    
                                    # Get all versions of the dependency
                                    dep_versions = self._get_package_versions(dep_name)
                                    
                                    # Check if any version satisfies both requirements
                                    compatible_dep_versions = [
                                        v for v in dep_versions 
                                        if pkg_dep_spec_set.contains(v) and direct_spec_set.contains(v)
                                    ]
                                    
                                    if not compatible_dep_versions:
                                        if dep_name not in conflicts:
                                            conflicts[dep_name] = {}
                                        conflicts[dep_name][pkg_name] = list(pkg_dep_spec_set)
                                        
                        except Exception:
                            continue
            except Exception as e:
                raise DependencyError(f"Error checking conflicts for {pkg_name}: {str(e)}")
                
        # Check transitive dependencies
        for pkg_name, pkg_specs in dependencies.items():
            if pkg_name in conflicts:
                continue
            try:
                response = requests.get(self.pypi_url.format(package=pkg_name))
                response.raise_for_status()
                pkg_data = response.json()
                
                pkg_versions = self._get_package_versions(pkg_name)
                pkg_spec_set = SpecifierSet(','.join(pkg_specs))
                compatible_versions = [str(v) for v in pkg_versions if pkg_spec_set.contains(v)]
                
                if compatible_versions:
                    latest_compatible = max(compatible_versions, key=parse)
                    release_data = [r for r in pkg_data['releases'][latest_compatible] if r.get('requires_dist')]
                    
                    if release_data:
                        for req in release_data[0].get('requires_dist', []):
                            try:
                                dep_name = req.split(' ')[0].lower()
                                if dep_name in dependencies:
                                    dep_specs = req.split('(')[1].split(')')[0] if '(' in req else ''
                                    pkg_dep_spec_set = SpecifierSet(dep_specs)
                                    direct_spec_set = SpecifierSet(','.join(dependencies[dep_name]))
                                    
                                    if not any(pkg_dep_spec_set.contains(Version(ver)) and direct_spec_set.contains(Version(ver)) 
                                             for ver in compatible_versions):
                                        if pkg_name not in conflicts:
                                            conflicts[pkg_name] = {}
                                        conflicts[pkg_name][dep_name] = list(pkg_dep_spec_set)
                            except Exception:
                                continue
                                
            except Exception:
                continue

        # Cache the results
        self.cache.store_conflicts(dependencies, conflicts)
        return conflicts

    def get_compatible_versions(self, package: str, conflict: Dict[str, List[str]]) -> List[str]:
        """Get list of versions compatible with all requirements"""
        try:
            # Convert conflict specs to lists for JSON serialization
            json_safe_conflict = {k: list(v) for k, v in conflict.items()}
            
            # Check cache first
            cached_versions = self.cache.get_compatible_versions(package, json_safe_conflict)
            if cached_versions:
                return cached_versions

            all_versions = self._get_package_versions(package)
            all_specs = set()
            
            # Collect all version specifications
            for specs in conflict.values():
                if isinstance(specs, (list, set)):
                    all_specs.update(specs)
            
            if not all_specs:
                return [str(v) for v in all_versions[:5]]  # Return top 5 versions if no specific requirements
                
            # Create a SpecifierSet from all requirements
            spec_set = SpecifierSet(','.join(all_specs))
            
            # Find versions that satisfy all requirements
            compatible_versions = [str(v) for v in all_versions if spec_set.contains(v)][:5]  # Limit to top 5 versions
            
            # Cache the results
            self.cache.store_compatible_versions(package, json_safe_conflict, compatible_versions)
            return compatible_versions
            
        except Exception as e:
            raise DependencyError(f"Error finding compatible versions for {package}: {str(e)}")

    def _get_package_versions(self, package: str) -> List[Version]:
        """Get available versions for a package from PyPI"""
        try:
            response = requests.get(self.pypi_url.format(package=package))
            response.raise_for_status()
            
            releases = response.json()['releases']
            versions = [parse(v) for v in releases.keys()]
            return sorted(versions, reverse=True)
            
        except Exception as e:
            raise DependencyError(f"Error fetching versions for {package} from PyPI: {str(e)}")
