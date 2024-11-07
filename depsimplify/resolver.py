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

        for package, specs in dependencies.items():
            try:
                # Get all version requirements for this package
                all_specs = SpecifierSet(','.join(specs))
                available_versions = self._get_package_versions(package)
                
                # Find versions that satisfy all requirements
                compatible_versions = [
                    str(v) for v in available_versions 
                    if all_specs.contains(v)
                ]
                
                if not compatible_versions:
                    conflicts[package] = {
                        'requirements': list(specs),  # Convert set to list for JSON serialization
                        'available': [str(v) for v in available_versions[:5]]  # Show top 5 versions
                    }
                    
            except Exception as e:
                raise DependencyError(f"Error checking conflicts for {package}: {str(e)}")
                
        # Cache the results
        self.cache.store_conflicts(dependencies, conflicts)
        return conflicts

    def get_compatible_versions(self, package: str, conflict: Dict[str, Set[str]]) -> List[str]:
        """Get list of versions compatible with all requirements"""
        try:
            # Convert set to list for JSON serialization
            json_safe_conflict = {
                'requirements': list(conflict.get('requirements', set()))
            }
            
            # Check cache first
            cached_versions = self.cache.get_compatible_versions(package, json_safe_conflict)
            if cached_versions:
                return cached_versions

            all_versions = self._get_package_versions(package)
            requirements = conflict.get('requirements', set())
            
            if not requirements:
                return [str(v) for v in all_versions[:5]]  # Return top 5 versions if no specific requirements
                
            # Create a SpecifierSet from all requirements
            spec_set = SpecifierSet(','.join(requirements))
            
            # Find versions that satisfy all requirements
            compatible_versions = [
                str(v) for v in all_versions 
                if spec_set.contains(v)
            ]
            
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
