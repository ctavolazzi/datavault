import pytest
from pathlib import Path
import yaml
import shutil
from project_manager.project_manager import ProjectManager, FileMove
from unittest.mock import patch

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure with test files"""
    # Create project structure YAML
    structure = {
        'root': {
            'description': 'Root project directory',
            'subdirs': {
                'src': {
                    'description': 'Source code directory',
                    'file_patterns': {
                        r'.*\.py$': 'src',
                        r'.*\.java$': 'src'
                    }
                },
                'docs': {
                    'description': 'Documentation directory',
                    'file_patterns': {
                        r'.*\.md$': 'docs',
                        r'.*\.txt$': 'docs'
                    }
                },
                'data': {
                    'description': 'Data directory',
                    'subdirs': {
                        'raw': {
                            'description': 'Raw data directory',
                            'file_patterns': {r'.*\.csv$': 'data/raw'}
                        },
                        'processed': {
                            'description': 'Processed data directory'
                        }
                    }
                }
            }
        }
    }
    
    # Write structure file
    with open(tmp_path / 'project_structure.yaml', 'w') as f:
        yaml.dump(structure, f)
    
    # Create some test files
    (tmp_path / 'test.py').write_text('print("test")')
    (tmp_path / 'readme.md').write_text('# Test Project')
    (tmp_path / 'data.csv').write_text('a,b,c')
    
    return tmp_path

def test_initialization(temp_project):
    """Test basic initialization of ProjectManager"""
    manager = ProjectManager(root_dir=temp_project)
    assert manager.root == temp_project
    assert manager.structure is not None
    assert not manager.dry_run

def test_dry_run_mode(temp_project):
    """Test dry run mode doesn't modify files"""
    # Create a file in wrong location
    test_file = temp_project / 'test.py'
    original_content = test_file.read_text()
    
    # Run in dry run mode
    manager = ProjectManager(root_dir=temp_project, dry_run=True)
    manager.reset()
    
    # Verify file hasn't moved
    assert test_file.exists()
    assert test_file.read_text() == original_content

def test_file_organization(temp_project):
    """Test files are moved to correct locations"""
    with patch('builtins.input', return_value='y'):
        manager = ProjectManager(root_dir=temp_project)
        manager.reset()
    
    # Check if files were moved to correct directories
    assert (temp_project / 'src' / 'test.py').exists()
    assert (temp_project / 'docs' / 'readme.md').exists()
    assert (temp_project / 'data' / 'raw' / 'data.csv').exists()

def test_backup_creation(temp_project):
    """Test backup is created before changes"""
    manager = ProjectManager(root_dir=temp_project)
    manager.reset()
    
    # Find backup directory
    backup_dirs = list(temp_project.glob('backup_*'))
    assert len(backup_dirs) == 1
    
    # Verify backup contains original files
    backup_dir = backup_dirs[0]
    assert (backup_dir / 'test.py').exists()
    assert (backup_dir / 'readme.md').exists()
    assert (backup_dir / 'data.csv').exists()

def test_empty_directory_cleanup(temp_project):
    """Test cleanup of empty directories"""
    # Create empty directory
    empty_dir = temp_project / 'empty'
    empty_dir.mkdir()
    
    manager = ProjectManager(root_dir=temp_project)
    manager.reset()
    
    # Verify empty directory was removed
    assert not empty_dir.exists()

def test_file_conflict_handling(temp_project):
    """Test handling of file naming conflicts"""
    # Create src directory first
    (temp_project / 'src').mkdir(exist_ok=True)
    
    # Create two files with same name in different locations
    (temp_project / 'test.py').write_text('original')
    (temp_project / 'src' / 'test.py').write_text('existing')
    
    manager = ProjectManager(root_dir=temp_project)
    manager.reset()
    
    # Verify both files exist with different names
    src_files = list((temp_project / 'src').glob('test*.py'))
    assert len(src_files) == 2

def test_invalid_structure_file():
    """Test handling of invalid structure file"""
    tmp_path = Path('temp_test_dir')
    tmp_path.mkdir(exist_ok=True)
    
    try:
        with open(tmp_path / 'project_structure.yaml', 'w') as f:
            f.write('invalid: [\nyaml: content')
        
        with pytest.raises(ValueError):
            ProjectManager(root_dir=tmp_path)
    finally:
        shutil.rmtree(tmp_path)

def test_analyze_output(temp_project, capsys):
    """Test analyze() output format"""
    manager = ProjectManager(root_dir=temp_project)
    manager.analyze()
    
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "Project Structure Analysis" in output
    assert "Current Directory Structure" in output
    assert "File Organization" in output

def test_file_analyzer_integration(temp_project):
    """Test integration with FileAnalyzer"""
    # Create a file without extension
    unknown_file = temp_project / 'unknown_file'
    unknown_file.write_text('PDF content')  # Content that might be recognized by magic
    
    manager = ProjectManager(root_dir=temp_project)
    moves = manager._analyze_files()
    
    # Verify FileAnalyzer was used to determine file type
    assert any(move.source == unknown_file for move in moves)

def test_structure_validation(temp_project):
    """Test validation of project structure"""
    # Create invalid structure
    with open(temp_project / 'project_structure.yaml', 'w') as f:
        yaml.dump(['invalid', 'structure'], f)
    
    with pytest.raises(ValueError, match="Project structure must be a dictionary"):
        ProjectManager(root_dir=temp_project)

def test_warning_suggestions_match_context(tmp_path):
    """Test that warning suggestions are contextually appropriate"""
    structure = {
        'src': {
            'description': 'Source code',
            'subdirs': {
                'models': {'description': 'Data models'},
                'core': {
                    'description': 'Core code',
                    'subdirs': {
                        'models': {'description': 'Core models'}  # Same name as src/models
                    }
                }
            }
        }
    }
    
    with open(tmp_path / "project_structure.yaml", "w") as f:
        yaml.dump(structure, f)
    
    with pytest.warns(UserWarning) as warning_info:
        manager = ProjectManager(root_dir=tmp_path)
        
    # Verify warning details
    warning = warning_info[0]
    warning_text = str(warning.message)
    
    # Check basic warning structure
    assert "Potential naming conflict detected" in warning_text
    assert "Directory name 'models' is used in multiple locations" in warning_text
    
    # Check that paths are mentioned
    assert "src/models" in warning_text
    assert "src/core/models" in warning_text
    
    # Check suggestions
    assert "Use more specific names" in warning_text
    # Check that at least one context-aware suggestion is present
    assert any(
        suggestion in warning_text 
        for suggestion in ['src_models', 'core_models']
    )

if __name__ == '__main__':
    pytest.main([__file__, '-v'])