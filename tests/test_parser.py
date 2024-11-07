import pytest
from depsimplify.dependency_parser import DependencyParser
from depsimplify.exceptions import DependencyError

def test_parse_requirements(tmp_path):
    parser = DependencyParser()
    
    # Create test requirements.txt
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("""
    requests>=2.25.0
    urllib3<2.0.0
    # Comment line
    flask==2.0.0
    """)
    
    deps = parser._parse_requirements(req_file.read_text().splitlines())
    
    assert 'requests' in deps
    assert 'urllib3' in deps
    assert 'flask' in deps
    assert '>=2.25.0' in deps['requests']
    assert '<2.0.0' in deps['urllib3']
    assert '==2.0.0' in deps['flask']

def test_parse_setup_py(tmp_path):
    parser = DependencyParser()
    
    # Create test setup.py
    setup_file = tmp_path / "setup.py"
    setup_file.write_text("""
from setuptools import setup

setup(
    name='test-project',
    version='0.1.0',
    install_requires=[
        'requests>=2.25.0',
        'urllib3<2.0.0',
    ],
)
    """)
    
    deps = parser._parse_setup_py(setup_file.read_text())
    
    assert 'requests' in deps
    assert 'urllib3' in deps
    assert '>=2.25.0' in deps['requests']
    assert '<2.0.0' in deps['urllib3']

def test_update_requirements(tmp_path):
    parser = DependencyParser()
    
    # Create test requirements.txt
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("""
    requests>=2.25.0
    urllib3<2.0.0
    flask==2.0.0
    """)
    
    resolved_deps = {
        'requests': '2.26.0',
        'urllib3': '1.26.0'
    }
    
    parser.update_requirements(resolved_deps, requirements_path=str(req_file))
    
    # Check updated content
    updated_content = req_file.read_text()
    assert 'requests==2.26.0' in updated_content
    assert 'urllib3==1.26.0' in updated_content
    assert 'flask==2.0.0' in updated_content
