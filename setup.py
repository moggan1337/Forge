#!/usr/bin/env python
"""Setup script for Forge transpiler."""

from setuptools import setup, find_packages

setup(
    name="forge-transpiler",
    version="0.1.0",
    description="AI-Assisted Language Transpiler",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Forge Team",
    author_email="team@forge-transpiler.dev",
    url="https://github.com/moggan1337/Forge",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "click>=8.1.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.7.0",
            "pre-commit>=3.5.0",
        ],
        "lsp": [
            "pygls>=1.0.0",
            "python-lsp-server>=1.8.0",
            "jedi>=0.19.0",
            "parso>=0.8.0",
        ],
        "all": [
            "tree-sitter>=0.20.0",
            "tree-sitter-languages>=1.7.0",
            "openai>=1.0.0",
            "anthropic>=0.10.0",
            "pygls>=1.0.0",
            "python-lsp-server>=1.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "forge=forge.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Translators",
    ],
    include_package_data=True,
    zip_safe=False,
)
