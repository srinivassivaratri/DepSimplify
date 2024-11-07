import json
import os
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta

class DependencyCache:
    """Cache for dependency resolution results"""
    
    def __init__(self, cache_dir: str = '.depsimplify'):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'cache.json')
        self.cache_expiry = timedelta(days=1)  # Cache expires after 1 day

    def initialize(self) -> None:
        """Initialize cache directory and file"""
        os.makedirs(self.cache_dir, exist_ok=True)
        if not os.path.exists(self.cache_file):
            self._save_cache({
                'conflicts': {},
                'compatible_versions': {},
                'resolutions': {},
                'last_updated': datetime.now().isoformat()
            })

    def _load_cache(self) -> Dict:
        """Load cache from file"""
        try:
            if not os.path.exists(self.cache_file):
                return {}
                
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
                
            # Check cache expiry
            last_updated = datetime.fromisoformat(cache.get('last_updated', '2000-01-01'))
            if datetime.now() - last_updated > self.cache_expiry:
                return {}
                
            return cache
        except Exception:
            return {}

    def _save_cache(self, cache_data: Dict) -> None:
        """Save cache to file"""
        try:
            cache_data['last_updated'] = datetime.now().isoformat()
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)
        except Exception:
            pass

    def get_conflicts(self, dependencies: Dict[str, List[str]]) -> Optional[Dict]:
        """Get cached conflicts for dependencies"""
        cache = self._load_cache()
        deps_key = json.dumps(dependencies, sort_keys=True)
        return cache.get('conflicts', {}).get(deps_key)

    def store_conflicts(self, dependencies: Dict[str, List[str]], conflicts: Dict) -> None:
        """Store conflicts in cache"""
        cache = self._load_cache()
        deps_key = json.dumps(dependencies, sort_keys=True)
        if 'conflicts' not in cache:
            cache['conflicts'] = {}
        cache['conflicts'][deps_key] = conflicts
        self._save_cache(cache)

    def get_compatible_versions(self, package: str, conflict: Dict[str, Set[str]]) -> Optional[List[str]]:
        """Get cached compatible versions"""
        cache = self._load_cache()
        conflict_key = json.dumps({'package': package, 'conflict': conflict}, sort_keys=True)
        return cache.get('compatible_versions', {}).get(conflict_key)

    def store_compatible_versions(self, package: str, conflict: Dict[str, Set[str]], versions: List[str]) -> None:
        """Store compatible versions in cache"""
        cache = self._load_cache()
        conflict_key = json.dumps({'package': package, 'conflict': conflict}, sort_keys=True)
        if 'compatible_versions' not in cache:
            cache['compatible_versions'] = {}
        cache['compatible_versions'][conflict_key] = versions
        self._save_cache(cache)

    def store_resolutions(self, resolved_deps: Dict[str, str]) -> None:
        """Store resolved dependencies"""
        cache = self._load_cache()
        if 'resolutions' not in cache:
            cache['resolutions'] = {}
        cache['resolutions'].update(resolved_deps)
        self._save_cache(cache)

    def get_resolutions(self) -> Dict[str, str]:
        """Get cached dependency resolutions"""
        cache = self._load_cache()
        return cache.get('resolutions', {})
