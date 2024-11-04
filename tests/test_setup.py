import pytest
from pathlib import Path
import yaml
from project_manager.setup import ProjectSetup, SetupError

def test_dry_run(temp_project_dir, caplog):
    """Test dry run mode doesn't create directories"""
    setup = ProjectSetup(root_dir=temp_project_dir, dry_run=True)
    
    success, errors = setup.setup()
    assert success
    assert not errors
    
    # Check that only project_structure.yaml exists
    files = list(temp_project_dir.glob('**/*'))
    assert len(files) == 1
    assert files[0].name == 'project_structure.yaml'
    
    # Verify logging messages
    assert "Would create directory" in caplog.text
    assert "Dry run mode: enabled" in caplog.text

def test_actual_setup(temp_project_dir, test_structure):
    """Test actual directory creation"""
    setup = ProjectSetup(root_dir=temp_project_dir)
    
    success, errors = setup.setup()
    assert success
    assert not errors
    
    # Get created paths
    created_dirs, created_files = setup.get_created_paths()
    
    # Verify all expected directories were created
    expected_dirs = {
        'src', 'src/core', 'src/utils',
        'docs', 'tests', 'tests/unit', 'tests/integration'
    }
    
    created_dir_names = {str(p.relative_to(temp_project_dir)) for p in created_dirs}
    assert created_dir_names == expected_dirs
    
    # Verify README files
    readme_files = [p for p in created_files if p.name == 'README.md']
    assert len(readme_files) == len(expected_dirs)
    
    # Check specific README content
    docs_readme = (temp_project_dir / 'docs' / 'README.md').read_text()
    assert 'Documentation directory' in docs_readme

def test_invalid_structure(tmp_path):
    """Test handling of invalid structure file"""
    # Create invalid YAML
    structure_file = tmp_path / 'project_structure.yaml'
    structure_file.write_text('invalid: [\nyaml: content')
    
    setup = ProjectSetup(root_dir=tmp_path)
    success, errors = setup.setup()
    
    assert not success
    assert len(errors) > 0
    assert any('YAML' in error for error in errors)

def test_existing_directories(temp_project_dir):
    """Test setup with existing directories"""
    # Create a directory and file beforehand
    existing_dir = temp_project_dir / 'src' / 'utils'
    existing_dir.mkdir(parents=True)
    existing_file = existing_dir / 'existing.py'
    existing_file.write_text('# Existing file')
    
    setup = ProjectSetup(root_dir=temp_project_dir)
    success, errors = setup.setup()
    
    assert success
    assert not errors
    # Verify existing file wasn't touched
    assert existing_file.read_text() == '# Existing file'

def test_readme_creation(temp_project_dir):
    """Test README creation with proper content"""
    setup = ProjectSetup(root_dir=temp_project_dir)
    success, errors = setup.setup()
    
    assert success
    assert not errors
    
    # Check core README content
    core_readme = (temp_project_dir / 'src' / 'core' / 'README.md').read_text()
    assert '# Core\n' in core_readme
    assert 'Core functionality' in core_readme
    
    # Check utils README content
    utils_readme = (temp_project_dir / 'src' / 'utils' / 'README.md').read_text()
    assert '# Utils\n' in utils_readme
    assert 'Utility functions' in utils_readme

def test_permission_error(temp_project_dir, monkeypatch):
    """Test handling of permission errors"""
    def mock_mkdir(*args, **kwargs):
        raise PermissionError("Permission denied")
    
    monkeypatch.setattr(Path, 'mkdir', mock_mkdir)
    
    setup = ProjectSetup(root_dir=temp_project_dir)
    success, errors = setup.setup()
    
    assert not success
    assert len(errors) > 0
    assert any('Permission denied' in error for error in errors)

def test_structure_validation(temp_project_dir):
    """Test structure validation"""
    # Create invalid structure (missing required fields)
    invalid_structure = {
        'src': {
            'subdirs': {
                'core': {}  # Missing description
            }
        }
    }
    
    structure_file = temp_project_dir / 'project_structure.yaml'
    with open(structure_file, 'w') as f:
        yaml.dump(invalid_structure, f)
    
    setup = ProjectSetup(root_dir=temp_project_dir)
    success, errors = setup.setup()
    
    assert success  # Should still succeed as description is optional
    
    # Verify directory was created
    assert (temp_project_dir / 'src' / 'core').is_dir()
    
    # Verify README was created with default description
    readme = (temp_project_dir / 'src' / 'core' / 'README.md').read_text()
    assert 'Directory for core' in readme

if __name__ == '__main__':
    pytest.main(['-v', __file__]) 