from typing import List, Dict
import pkg_resources
from packaging.version import Version, parse
from .exceptions import DependencyError

def get_installed_version(package: str) -> str:
    """Get the installed version of a package"""
    try:
        return pkg_resources.get_distribution(package).version
    except pkg_resources.DistributionNotFound:
        return None

def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two version strings
    Returns:
        -1 if version1 < version2
        0 if version1 == version2
        1 if version1 > version2
    """
    try:
        v1 = parse(version1)
        v2 = parse(version2)
        
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        else:
            return 0
    except Exception as e:
        raise DependencyError(f"Invalid version format: {str(e)}")

def format_requirement(package: str, version: str) -> str:
    """Format package requirement string"""
    return f"{package}=={version}"

def parse_version_specs(specs: List[str]) -> Dict[str, List[Version]]:
    """Parse version specifications into min/max versions"""
    result = {'min': [], 'max': []}
    
    for spec in specs:
        try:
            op = spec[:2] if spec[1] in ('=', '>') else spec[0]
            version = spec[2:] if len(op) == 2 else spec[1:]
            v = parse(version)
            
            if op in ('>=', '>'):
                result['min'].append(v)
            elif op in ('<=', '<'):
                result['max'].append(v)
                
        except Exception:
            continue
            
    return result
