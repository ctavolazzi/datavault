import pytest
from pathlib import Path
import yaml

@pytest.fixture
def test_structure():
    """Return a test project structure"""
    return {
        'src': {
            'description': 'Source code directory',
            'subdirs': {
                'core': {'description': 'Core functionality'},
                'utils': {'description': 'Utility functions'}
            }
        },
        'docs': {
            'description': 'Documentation directory'
        },
        'tests': {
            'description': 'Test directory',
            'subdirs': {
                'unit': {'description': 'Unit tests'},
                'integration': {'description': 'Integration tests'}
            }
        }
    }

@pytest.fixture
def temp_project_dir(tmp_path, test_structure):
    """Create a temporary project directory with test structure"""
    # Write structure file
    structure_file = tmp_path / 'project_structure.yaml'
    with open(structure_file, 'w') as f:
        yaml.dump(test_structure, f)
    
    return tmp_path

@pytest.fixture
def setup_with_structure(temp_project_dir):
    """Return ProjectSetup instance with test structure"""
    from project_manager.setup import ProjectSetup
    return ProjectSetup(root_dir=temp_project_dir) 