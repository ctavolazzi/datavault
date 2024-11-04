# DataVault Project Structure

## Overview
DataVault is organized into a hierarchical directory structure that separates source code, data, documentation, and outputs.

## Directory Structure

### 📁 src/
Source code for the project
- 📁 `api/` - API endpoints and interfaces
- 📁 `collectors/` - Data collection modules
- 📁 `core/` - Core functionality and base classes
- 📁 `handlers/` - Data handling code
- 📁 `scripts/` - Automation scripts
- 📁 `utils/` - Utility functions and helpers
- 📁 `tests/` - Source-level test files

### 📁 datasets/
Data storage directories
- 📁 `raw/` - Original, immutable data
- 📁 `processed/` - Cleaned, transformed data
- 📁 `interim/` - Intermediate processing steps
- 📁 `external/` - Third-party data
- 📁 `news/`
  - 📁 `raw/` - Raw news data collections
  - 📁 `processed/` - Processed news articles

### 📁 docs/
Project documentation
- 📁 `api/` - API documentation and specs
- 📁 `guides/` - User and developer guides
- 📁 `references/` - Reference materials
- 📁 `tests/`
  - 📁 `unit/` - Unit test documentation
  - 📁 `integration/` - Integration test documentation
  - 📁 `fixtures/` - Test data documentation

### 📁 output/
Generated outputs
- 📁 `reports/` - Analysis reports
- 📁 `figures/` - Visualizations and plots
- 📁 `exports/` - Exported datasets
- 📁 `tests/`
  - 📁 `unit/` - Unit test outputs
  - 📁 `integration/` - Integration test outputs
  - 📁 `fixtures/` - Test output fixtures

### 📁 config/
Configuration files
- 📁 `env/` - Environment configurations
- 📁 `schemas/` - Data validation schemas

### 📁 logs/
Log files
- 📁 `app/` - Application logs
- 📁 `audit/` - Audit trail logs

### 📁 tests/
Project-level test suites
- 📁 `unit/` - Unit tests
- 📁 `integration/` - Integration tests
- 📁 `fixtures/` - Test data and fixtures

### 📁 src/scripts/
Automation scripts
- 📁 `setup/` - Project setup and maintenance scripts
  - `backup_project.py` - Project backup utilities
  - `generate_filetree.py` - Directory structure generation
  - `manage_backups.py` - Backup management tools
  - `reset_project.py` - Project reset utilities
  - `setup_project.py` - Initial project setup
  - `verify_backup.py` - Backup verification tools

## File Patterns
- Documentation files: `*.md`, `*.txt` → `docs/`
- API specifications: `*.yaml` → `docs/api/`
- Test files: `*_test.py` → `src/tests/`
