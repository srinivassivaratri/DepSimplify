import click
import os
from typing import List, Dict
from .dependency_parser import DependencyParser
from .resolver import DependencyResolver
from .cache import DependencyCache
from .exceptions import DependencyError

@click.group()
def cli():
    """DepSimplify - Simplify your Python dependency management"""
    pass

@cli.command()
def init():
    """Initialize dependency tracking for the project"""
    try:
        if not os.path.exists('requirements.txt') and not os.path.exists('setup.py'):
            click.echo("No requirements.txt or setup.py found. Creating requirements.txt...")
            with open('requirements.txt', 'w') as f:
                f.write("# Project dependencies\n")
        
        cache = DependencyCache()
        cache.initialize()
        click.echo("✅ Initialized DepSimplify successfully!")
        
    except Exception as e:
        click.echo(f"❌ Error initializing DepSimplify: {str(e)}", err=True)

@cli.command()
def check():
    """Check for dependency conflicts"""
    try:
        parser = DependencyParser()
        resolver = DependencyResolver()
        
        # Parse dependencies
        deps = parser.parse_project_dependencies()
        click.echo("📝 Analyzing dependencies...")
        
        # Check for conflicts
        conflicts = resolver.find_conflicts(deps)
        
        if not conflicts:
            click.echo("✅ No conflicts found!")
            return
        
        click.echo("\n⚠️ Found the following conflicts:")
        for pkg, conflict in conflicts.items():
            click.echo(f"\n{pkg}:")
            for dep, versions in conflict.items():
                click.echo(f"  - Required by {dep}: {versions}")
                
    except DependencyError as e:
        click.echo(f"❌ Dependency error: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"❌ Error checking dependencies: {str(e)}", err=True)

@cli.command()
def resolve():
    """Resolve detected conflicts interactively"""
    try:
        parser = DependencyParser()
        resolver = DependencyResolver()
        cache = DependencyCache()
        
        # Parse dependencies
        deps = parser.parse_project_dependencies()
        conflicts = resolver.find_conflicts(deps)
        
        if not conflicts:
            click.echo("✅ No conflicts to resolve!")
            return
            
        resolved_deps = {}
        for pkg, conflict in conflicts.items():
            click.echo(f"\n📦 Resolving conflict for {pkg}")
            versions = resolver.get_compatible_versions(pkg, conflict)
            
            if not versions:
                click.echo(f"❌ No compatible versions found for {pkg}")
                continue
                
            # Interactive version selection
            click.echo("\nAvailable versions:")
            for idx, version in enumerate(versions, 1):
                click.echo(f"{idx}. {version}")
                
            version_idx = click.prompt(
                "Select version number",
                type=click.IntRange(1, len(versions)),
                default=1
            )
            
            resolved_deps[pkg] = versions[version_idx - 1]
            
        # Update requirements.txt with resolved dependencies
        if resolved_deps:
            parser.update_requirements(resolved_deps)
            cache.store_resolutions(resolved_deps)
            click.echo("\n✅ Successfully resolved conflicts!")
            
    except DependencyError as e:
        click.echo(f"❌ Dependency error: {str(e)}", err=True)
    except Exception as e:
        click.echo(f"❌ Error resolving conflicts: {str(e)}", err=True)

if __name__ == '__main__':
    cli()
