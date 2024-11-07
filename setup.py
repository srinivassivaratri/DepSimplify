from setuptools import setup, find_packages

setup(
    name="depsimplify",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
        "requests>=2.25.0",
        "packaging>=21.0",
    ],
    entry_points={
        "console_scripts": [
            "depsimplify=depsimplify.cli:cli",
        ],
    },
    author="DepSimplify Team",
    author_email="info@depsimplify.dev",
    description="A Python dependency management tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/depsimplify/depsimplify",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.9",
)
