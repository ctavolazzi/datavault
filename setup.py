from setuptools import setup, find_packages
from pathlib import Path
import os
import sys

def initialize_datavault():
    """Initialize DataVault directory structure after installation"""
    base_dirs = [
        'datasets',
        'config',
        'logs',
        'output/figures',
        '.index'
    ]
    
    print("\nInitializing DataVault directory structure...")
    
    for dir_path in base_dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True)
            print(f"Created {dir_path}")

# Read README.md with explicit UTF-8 encoding
try:
    with open("README.md", encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = ""

# Main setup configuration
setup(
    name="datavault",
    version="0.1",
    author="Your Name",
    author_email="your.email@example.com",
    description="A data processing and analysis system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        'pyyaml',
        'tqdm',
        'python-magic-bin; platform_system == "Windows"',
        'python-magic; platform_system != "Windows"',
        'filelock',
        'pytest',
        'click',
        'pandas',
        'numpy',
        'loguru',
        'python-dotenv',
        'pycodestyle',
        'Pillow',
        'networkx',
        'matplotlib',
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'black',
            'isort',
            'flake8',
            'pre-commit',
            'mypy',
        ],
        'docs': [
            'sphinx',
            'sphinx-rtd-theme',
        ],
        'viz': ['networkx', 'matplotlib'],
    },
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'datavault=datavault.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)

# Post-installation setup
if __name__ == "__main__":
    # Check if this is an install command
    if "install" in sys.argv or "develop" in sys.argv:
        try:
            initialize_datavault()
            print("\nDataVault initialized successfully!")
            print("\nNext steps:")
            print("1. Run 'datavault welcome' to see available commands")
            print("2. Run 'datavault summary' to analyze your current directory")
            print("3. Check the README.md for more detailed documentation")
        except Exception as e:
            print(f"\nError during initialization: {str(e)}")
            print("You can manually initialize later using 'datavault init'")
