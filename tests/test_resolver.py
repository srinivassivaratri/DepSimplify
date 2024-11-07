import pytest
from depsimplify.resolver import DependencyResolver
from depsimplify.exceptions import DependencyError

def test_find_conflicts():
    resolver = DependencyResolver()
    
    # Test with compatible dependencies
    deps = {
        'requests': ['>=2.25.0'],
        'urllib3': ['>=1.26.0']
    }
    
    conflicts = resolver.find_conflicts(deps)
    assert not conflicts
    
    # Test with conflicting dependencies
    deps = {
        'requests': ['>=2.25.0'],
        'urllib3': ['<1.20.0']  # Conflicts with requests
    }
    
    conflicts = resolver.find_conflicts(deps)
    assert 'urllib3' in conflicts

def test_get_compatible_versions():
    resolver = DependencyResolver()
    
    conflict = {
        'requirements': {'>=1.26.0', '<2.0.0'}
    }
    
    versions = resolver.get_compatible_versions('urllib3', conflict)
    assert versions
    assert all('1.' in v for v in versions)

def test_invalid_package():
    resolver = DependencyResolver()
    
    with pytest.raises(DependencyError):
        resolver.get_compatible_versions('this-package-does-not-exist', {})
