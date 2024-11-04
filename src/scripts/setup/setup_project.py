import os
import sys
import logging
import subprocess
from pathlib import Path
import yaml
from typing import List, Dict

class ProjectSetup:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent.parent
        self.directories = [
            'src/api',
            'src/collectors',
            'src/core',
            'src/handlers',
            'src/utils',
            'src/tests',
            'datasets/raw',
            'datasets/processed',
            'datasets/interim',
            'datasets/external',
            'datasets/news/raw',
            'datasets/news/processed',
            'docs/api',
            'docs/guides',
            'docs/references',
            'docs/tests',
            'output/reports',
            'output/figures',
            'output/exports',
            'config/env',
            'config/schemas',
            'logs/app',
            'logs/audit',
            'tests/unit',
            'tests/integration',
            'tests/fixtures'
        ]
        self.setup_initial_logging()

    def setup_initial_logging(self) -> None:
        """Set up initial logging before any operations"""
        log_dir = self.root_dir / 'logs' / 'app'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'setup.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ProjectSetup')

    def create_directory_structure(self) -> None:
        """Create the project directory structure with .gitkeep files"""
        self.logger.info("Creating directory structure...")
        try:
            for directory in self.directories:
                dir_path = self.root_dir / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                (dir_path / '.gitkeep').touch()
            self.logger.info("Directory structure created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create directory structure: {str(e)}")
            raise

    def setup_virtual_environment(self) -> None:
        """Create and initialize virtual environment"""
        self.logger.info("Setting up virtual environment...")
        venv_path = self.root_dir / 'venv'
        
        if venv_path.exists():
            self.logger.info("Virtual environment already exists")
            return

        try:
            subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], 
                         check=True, 
                         capture_output=True)
            
            # Determine pip path based on platform
            pip_path = venv_path / ('Scripts' if os.name == 'nt' else 'bin') / 'pip'
            
            # Upgrade pip
            subprocess.run([str(pip_path), 'install', '--upgrade', 'pip'],
                         check=True,
                         capture_output=True)
            
            self.logger.info("Virtual environment created successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create virtual environment: {e.stderr.decode()}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating virtual environment: {str(e)}")
            raise

    def install_dependencies(self) -> None:
        """Install project dependencies from requirements.txt"""
        requirements_file = self.root_dir / 'requirements.txt'
        if not requirements_file.exists():
            self.logger.warning("requirements.txt not found - skipping dependency installation")
            return

        self.logger.info("Installing dependencies...")
        pip_path = self.root_dir / 'venv' / ('Scripts' if os.name == 'nt' else 'bin') / 'pip'
        
        try:
            subprocess.run([str(pip_path), 'install', '-r', str(requirements_file)],
                         check=True,
                         capture_output=True)
            self.logger.info("Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install dependencies: {e.stderr.decode()}")
            raise

    def create_config_files(self) -> None:
        """Create initial configuration files"""
        self.logger.info("Creating configuration files...")
        try:
            config = {
                'environment': 'development',
                'logging': {
                    'level': 'INFO',
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'handlers': {
                        'file': {
                            'path': 'logs/app/app.log',
                            'max_bytes': 10485760,  # 10MB
                            'backup_count': 5
                        }
                    }
                },
                'paths': {
                    'data': 'datasets',
                    'output': 'output',
                    'logs': 'logs'
                },
                'backup': {
                    'enabled': True,
                    'interval': '1d',
                    'retention': '30d',
                    'paths': ['datasets/raw', 'datasets/processed']
                }
            }
            
            config_path = self.root_dir / 'config' / 'env' / 'default.yaml'
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            self.logger.info("Configuration files created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create configuration files: {str(e)}")
            raise

    def setup_gitignore(self) -> None:
        """Create or update .gitignore file"""
        self.logger.info("Setting up .gitignore...")
        gitignore_path = self.root_dir / '.gitignore'
        
        gitignore_entries = [
            '# Virtual Environment',
            'venv/',
            'env/',
            '.env',
            '# Python',
            '__pycache__/',
            '*.py[cod]',
            '*.so',
            '# Logs',
            'logs/',
            '*.log',
            '# Output',
            'output/',
            '# IDE',
            '.idea/',
            '.vscode/',
            '# OS',
            '.DS_Store',
            'Thumbs.db'
        ]

        try:
            with open(gitignore_path, 'w') as f:
                f.write('\n'.join(gitignore_entries))
            self.logger.info(".gitignore created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create .gitignore: {str(e)}")
            raise

    def run(self) -> None:
        """Execute the complete setup process"""
        try:
            self.logger.info("Starting project setup...")
            
            self.create_directory_structure()
            self.setup_virtual_environment()
            self.install_dependencies()
            self.create_config_files()
            self.setup_gitignore()
            
            self.logger.info("Project setup completed successfully")
        except Exception as e:
            self.logger.error(f"Project setup failed: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    setup = ProjectSetup()
    setup.run()