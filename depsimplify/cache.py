import os
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

class DependencyCache:
    """Cache for dependency resolution results using SQLite"""
    
    def __init__(self, cache_dir: str = '.depsimplify'):
        self.cache_dir = cache_dir
        self.db_file = os.path.join(cache_dir, 'cache.db')
        self.cache_expiry = timedelta(days=1)  # Cache expires after 1 day

    def initialize(self) -> None:
        """Initialize SQLite database and create required tables"""
        os.makedirs(self.cache_dir, exist_ok=True)
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Create tables for different types of cache data
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conflicts (
                        dependencies_key TEXT PRIMARY KEY,
                        conflicts_data TEXT NOT NULL,
                        last_updated TIMESTAMP NOT NULL
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS compatible_versions (
                        conflict_key TEXT PRIMARY KEY,
                        versions TEXT NOT NULL,
                        last_updated TIMESTAMP NOT NULL
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resolutions (
                        package TEXT PRIMARY KEY,
                        version TEXT NOT NULL,
                        last_updated TIMESTAMP NOT NULL
                    )
                ''')
                
                # Create indices for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_conflicts_last_updated ON conflicts(last_updated)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_compatible_versions_last_updated ON compatible_versions(last_updated)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_resolutions_last_updated ON resolutions(last_updated)')
                
                conn.commit()
        except sqlite3.Error as e:
            os.makedirs(self.cache_dir, exist_ok=True)  # Ensure directory exists
            if os.path.exists(self.db_file):
                os.remove(self.db_file)  # Remove corrupted database
            raise Exception(f"Failed to initialize cache database: {str(e)}")

    def _is_cache_valid(self, last_updated: str) -> bool:
        """Check if cache entry is still valid"""
        if not last_updated:
            return False
        try:
            updated_time = datetime.fromisoformat(last_updated)
            return datetime.now() - updated_time <= self.cache_expiry
        except (ValueError, TypeError):
            return False

    def get_conflicts(self, dependencies: Dict[str, List[str]]) -> Optional[Dict]:
        """Get cached conflicts for dependencies"""
        if not dependencies:
            return None
            
        deps_key = json.dumps(dependencies, sort_keys=True)
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT conflicts_data, last_updated FROM conflicts WHERE dependencies_key = ?',
                    (deps_key,)
                )
                row = cursor.fetchone()
                
                if row and self._is_cache_valid(row[1]):
                    return json.loads(row[0])
                return None
                
        except (sqlite3.Error, json.JSONDecodeError):
            return None

    def store_conflicts(self, dependencies: Dict[str, List[str]], conflicts: Dict) -> None:
        """Store conflicts in SQLite cache"""
        if not dependencies or not conflicts:
            return
            
        deps_key = json.dumps(dependencies, sort_keys=True)
        conflicts_data = json.dumps(conflicts)
        last_updated = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT OR REPLACE INTO conflicts 
                       (dependencies_key, conflicts_data, last_updated) 
                       VALUES (?, ?, ?)''',
                    (deps_key, conflicts_data, last_updated)
                )
                conn.commit()
        except sqlite3.Error:
            pass

    def get_compatible_versions(self, package: str, conflict: Dict[str, List[str]]) -> Optional[List[str]]:
        """Get cached compatible versions"""
        if not package or not conflict:
            return None
            
        conflict_key = json.dumps({'package': package, 'conflict': conflict}, sort_keys=True)
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT versions, last_updated FROM compatible_versions WHERE conflict_key = ?',
                    (conflict_key,)
                )
                row = cursor.fetchone()
                
                if row and self._is_cache_valid(row[1]):
                    return json.loads(row[0])
                return None
                
        except (sqlite3.Error, json.JSONDecodeError):
            return None

    def store_compatible_versions(self, package: str, conflict: Dict[str, List[str]], versions: List[str]) -> None:
        """Store compatible versions in SQLite cache"""
        if not package or not conflict or not versions:
            return
            
        conflict_key = json.dumps({'package': package, 'conflict': conflict}, sort_keys=True)
        versions_data = json.dumps(versions)
        last_updated = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT OR REPLACE INTO compatible_versions 
                       (conflict_key, versions, last_updated) 
                       VALUES (?, ?, ?)''',
                    (conflict_key, versions_data, last_updated)
                )
                conn.commit()
        except sqlite3.Error:
            pass

    def store_resolutions(self, resolved_deps: Dict[str, str]) -> None:
        """Store resolved dependencies in SQLite cache"""
        if not resolved_deps:
            return
            
        last_updated = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                for package, version in resolved_deps.items():
                    if package and version:
                        cursor.execute(
                            '''INSERT OR REPLACE INTO resolutions 
                               (package, version, last_updated) 
                               VALUES (?, ?, ?)''',
                            (package, version, last_updated)
                        )
                conn.commit()
        except sqlite3.Error:
            pass

    def get_resolutions(self) -> Dict[str, str]:
        """Get cached dependency resolutions"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''SELECT package, version, last_updated 
                       FROM resolutions 
                       WHERE last_updated > ?''',
                    ((datetime.now() - self.cache_expiry).isoformat(),)
                )
                return {row[0]: row[1] for row in cursor.fetchall() if row[0] and row[1]}
                
        except sqlite3.Error:
            return {}
