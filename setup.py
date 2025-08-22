#!/usr/bin/env python3
"""
Network Topology Analyzer Setup Script
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="network-topology-analyzer",
    version="1.0.0",
    author="Network Analysis Team",
    author_email="team@networkanalyzer.com",
    description="Automated network topology generation and analysis from Cisco configuration files",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/network-topology-analyzer",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
        "web": [
            "flask>=2.3.0",
            "flask-socketio>=5.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "network-analyzer=main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.json", "*.txt"],
    },
    zip_safe=False,
)