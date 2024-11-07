# DepSimplify

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A Python CLI tool for automated dependency management and conflict resolution in Python projects. DepSimplify helps you manage complex dependency relationships, detect and resolve conflicts, and maintain a healthy Python environment.

## Features

- 📦 **Automated Dependency Resolution**: Parse and analyze dependencies from requirements.txt and setup.py files
- 🔍 **Conflict Detection**: Automatically identify version conflicts between direct and transitive dependencies
- 🛠️ **Interactive Resolution**: Resolve conflicts with suggested compatible versions
- ⚡ **Performance Optimized**: SQLite-based caching system for faster dependency resolution
- 🔒 **SSL Compliant**: Modern SSL standards support through urllib3 2.0.0+
- 🧪 **Comprehensive Testing**: Built-in test suite for reliable dependency management

## Installation

```bash
pip install depsimplify
```

## Quick Start

1. Initialize DepSimplify in your project:
```bash
depsimplify init
```

2. Check for dependency conflicts:
```bash
depsimplify check
```

3. Resolve any detected conflicts:
```bash
depsimplify resolve
```

## Usage Examples

### Check Dependencies

```bash
$ depsimplify check
📝 Analyzing dependencies...
✅ No conflicts found!
```

### Resolve Conflicts

When conflicts are found:
```bash
$ depsimplify check
📝 Analyzing dependencies...
⚠️ Found the following conflicts:
urllib3:
  - Required by requests: >=1.25.3
  - Current version: ==1.24.0

$ depsimplify resolve
📦 Resolving conflict for urllib3
Available versions:
1. 2.0.7
2. 2.0.6
3. 2.0.5
Select version number: 1
✅ Successfully resolved conflicts!
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/depsimplify.git
cd depsimplify
```

2. Install dependencies:
```bash
pip install -e .
```

3. Run tests:
```bash
python -m pytest tests/
```

## Project Structure

```
depsimplify/
├── __init__.py
├── cli.py            # Command-line interface
├── dependency_parser.py  # Parse requirements files
├── resolver.py       # Dependency resolution logic
├── cache.py         # SQLite caching system
├── exceptions.py    # Custom exceptions
└── utils.py         # Utility functions
```

## Testing

DepSimplify uses pytest for testing. Run the test suite:

```bash
python -m pytest tests/
```

The test suite includes:
- Dependency parsing tests
- Conflict detection tests
- Version compatibility tests
- Cache system tests

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [pip](https://pip.pypa.io/) for inspiration on dependency resolution
- [packaging](https://packaging.pypa.org/) for Python package version handling
- [click](https://click.palletsprojects.com/) for CLI interface

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/yourusername/depsimplify/issues) on GitHub.
