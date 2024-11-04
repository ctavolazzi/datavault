import pytest
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from project_manager.project_indexer import ProjectIndexer

class TestProjectIndexer:
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with test files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Create test directory structure
            (project_dir / "src" / "utils").mkdir(parents=True)
            (project_dir / "docs").mkdir()
            (project_dir / "tests").mkdir()
            
            # Create some test files
            (project_dir / "src" / "utils" / "test.py").write_text("print('hello')")
            (project_dir / "docs" / "readme.md").write_text("# Test Project")
            (project_dir / "tests" / "test_main.py").write_text("def test_something(): pass")
            
            yield project_dir
    
    @pytest.fixture
    def indexer(self, temp_project_dir):
        """Create ProjectIndexer instance with temp directory"""
        return ProjectIndexer(temp_project_dir)
    
    def test_init_creates_index_directory(self, temp_project_dir):
        """Test that initialization creates the .index directory"""
        indexer = ProjectIndexer(temp_project_dir)
        assert (temp_project_dir / '.index').exists()
        assert (temp_project_dir / '.index').is_dir()
    
    def test_index_project_structure(self, indexer):
        """Test that index_project creates correct structure"""
        index = indexer.index_project()
        
        assert 'timestamp' in index
        assert 'files' in index
        assert 'directories' in index
        assert 'metadata' in index
        assert all(key in index['metadata'] for key in ['total_files', 'total_dirs', 'file_types'])
    
    def test_file_counting(self, indexer):
        """Test that file and directory counts are correct"""
        index = indexer.index_project()
        
        # Debug: print all directories being counted
        print("\nDirectories found:")
        for d in index['directories']:
            print(f"- {d['path']}")
        
        assert index['metadata']['total_files'] == 3  # test.py, readme.md, test_main.py
        assert index['metadata']['total_dirs'] == 3   # src/utils, docs, tests
    
    def test_file_info_content(self, indexer, temp_project_dir):
        """Test that file info contains correct metadata"""
        index = indexer.index_project()
        test_py_file = next(f for f in index['files'] 
                           if f['path'] == 'src/utils/test.py')
        
        assert test_py_file['name'] == 'test.py'
        assert test_py_file['type'] == '.py'
        assert test_py_file['size'] > 0
        assert test_py_file['encoding'] is not None
        
        # Verify timestamps are recent
        created = datetime.fromisoformat(test_py_file['created'])
        modified = datetime.fromisoformat(test_py_file['modified'])
        assert datetime.now() - created < timedelta(minutes=1)
        assert datetime.now() - modified < timedelta(minutes=1)
    
    def test_file_types_tracking(self, indexer):
        """Test that file types are correctly tracked"""
        index = indexer.index_project()
        
        assert index['metadata']['file_types'] == {
            '.py': 2,   # test.py and test_main.py
            '.md': 1    # readme.md
        }
    
    def test_index_file_creation(self, indexer, temp_project_dir):
        """Test that index file is created and contains valid JSON"""
        indexer.index_project()
        index_file = temp_project_dir / '.index' / 'project_index.json'
        
        assert index_file.exists()
        
        # Verify JSON is valid and has expected structure
        with open(index_file) as f:
            data = json.load(f)
            assert 'files' in data
            assert 'directories' in data
            assert 'metadata' in data
    
    def test_skip_index_directory(self, indexer, temp_project_dir):
        """Test that .index directory is not included in the index"""
        index = indexer.index_project()
        
        # Create a file in .index directory
        (temp_project_dir / '.index' / 'test.txt').write_text('test')
        
        # Verify no paths contain '.index'
        assert not any('.index' in f['path'] for f in index['files'])
        assert not any('.index' in d['path'] for d in index['directories'])