class DependencyError(Exception):
    """Base exception for dependency-related errors"""
    pass

class ParseError(DependencyError):
    """Error parsing dependency specifications"""
    pass

class ResolutionError(DependencyError):
    """Error resolving dependencies"""
    pass

class CacheError(DependencyError):
    """Error with dependency cache"""
    pass
