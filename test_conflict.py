from depsimplify.resolver import DependencyResolver

# Create test case with known conflict
deps = {
    'requests': ['>=2.25.0'],
    'urllib3': ['==1.24.0']  # This conflicts with requests
}

resolver = DependencyResolver()
conflicts = resolver.find_conflicts(deps)
print(f"Detected conflicts: {conflicts}")
