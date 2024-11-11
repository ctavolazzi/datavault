from setuptools import setup, find_packages

setup(
    name="datavault-cli",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "click>=8.0.0",
        "openai>=1.0.0",
        "python-dotenv>=0.19.0",
        "freezegun>=1.5.0",
    ],
    entry_points={
        "console_scripts": [
            "datavault=ai_analyzer.cli:cli",
        ],
    },
)