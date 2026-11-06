# Poetry Development Guide for MedEval

This guide explains how to use Poetry for dependency management in MedEval.

## Table of Contents
1. [Overview](#overview)
2. [Initial Setup](#initial-setup)
3. [Common Commands](#common-commands)
4. [Managing Dependencies](#managing-dependencies)
5. [Running Tests](#running-tests)
6. [Troubleshooting](#troubleshooting)

---

## Overview

MedEval uses Poetry for:
- ✅ **Dependency Management** - Consistent package versions across environments
- ✅ **Virtual Environment** - Isolated Python environment in `.venv/`
- ✅ **Reproducible Builds** - Lock file ensures exact versions
- ✅ **Development Tools** - pytest, flake8, coverage integrated

**Python Version:** 3.12+  
**Poetry Version:** 2.4.1+

---

## Initial Setup

### 1. Install Poetry

**Windows PowerShell:**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

**Linux/Mac:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Configure Poetry

```bash
# Set Poetry to create .venv in project directory
poetry config virtualenvs.in-project true

# Verify configuration
poetry config virtualenvs.in-project
# Should output: true
```

### 3. Create Virtual Environment

```bash
cd C:\Users\Tay\Documents\GitHub\medeval

# Use specific Python version (e.g., Python 3.12.1)
poetry env use "C:\Users\Tay\AppData\Local\Programs\Python\Python312\python.exe"

# Or use system default Python 3.12
poetry env use python3.12
```

**Output:**
```
Creating virtualenv medeval in C:\Users\Tay\Documents\GitHub\medeval\.venv
Using virtualenv: C:\Users\Tay\Documents\GitHub\medeval\.venv
```

### 4. Install Dependencies

**Install core + OpenAI:**
```bash
poetry install --extras openai
```

**Install only core (no OpenAI):**
```bash
poetry install
```

**Install with development tools:**
```bash
poetry install --extras openai --with dev
```

---

## Common Commands

### Using the Helper Script

For convenience, use `poetry.ps1` (Windows) to avoid typing the full Poetry path:

```powershell
# Show help
.\poetry.ps1

# Install dependencies
.\poetry.ps1 install --extras openai

# Run a command in the virtual environment
.\poetry.ps1 run medeval list-runs

# Run tests
.\poetry.ps1 run python tests\software\test_full_pipeline.py

# Add a new package
.\poetry.ps1 add requests

# Update dependencies
.\poetry.ps1 update
```

### Direct Poetry Commands

```bash
# Show environment info
poetry env info

# List installed packages
poetry show

# Show dependency tree
poetry show --tree

# Check for outdated packages
poetry show --outdated

# Run a command
poetry run python script.py
poetry run medeval run --dataset datasets/clinical_cases.jsonl

# Activate poetry shell (interactive)
poetry shell

# Deactivate
exit
```

---

## Managing Dependencies

### Adding Dependencies

**Production Dependency:**
```bash
poetry add requests
poetry add "numpy>=1.20"
```

**Development Dependency:**
```bash
poetry add --group dev black
poetry add --group dev "mypy>=1.0"
```

**Optional Dependency:**
```bash
poetry add --optional anthropic
```

### Removing Dependencies

```bash
poetry remove requests
poetry remove --group dev black
```

### Updating Dependencies

```bash
# Update all dependencies
poetry update

# Update specific package
poetry update openai

# Update to latest within version constraints
poetry update pyyaml
```

### Viewing Dependencies

```bash
# List all installed packages
poetry show

# Show specific package info
poetry show openai

# Show dependency tree
poetry show --tree

# Show only direct dependencies
poetry show --only main
```

---

## Running Tests

### Full Integration Test

```bash
# Using helper script
.\poetry.ps1 run python tests\software\test_full_pipeline.py

# Direct
poetry run python tests\software\test_full_pipeline.py
```

### Unit Tests with pytest

```bash
# Run all unit tests
.\poetry.ps1 run pytest tests/unit -v

# Run specific test file
.\poetry.ps1 run pytest tests/unit/application/test_openai_integration.py -v

# Run with coverage
.\poetry.ps1 run pytest tests/unit --cov=src/medeval --cov-report=html
```

### Using MedEval CLI

```bash
# List runs
.\poetry.ps1 run medeval list-runs --limit 10

# Run evaluation
.\poetry.ps1 run medeval run --dataset datasets/clinical_cases.jsonl

# View report
.\poetry.ps1 run medeval report --run 20260828_164943

# Clean old runs
.\poetry.ps1 run medeval clean --keep 10
```

### Code Quality Checks

```bash
# Lint with flake8
.\poetry.ps1 run flake8 src/medeval

# Check syntax
.\poetry.ps1 run python -m compileall src/medeval

# Run all quality checks
.\poetry.ps1 run flake8 src/medeval
.\poetry.ps1 run pytest tests/unit -v
```

---

## Environment Management

### Environment Info

```bash
# Show environment details
poetry env info

# Output:
# Virtualenv
# Python:         3.12.4
# Implementation: CPython
# Path:           C:\Users\Tay\Documents\GitHub\medeval\.venv
# Executable:     C:\Users\Tay\Documents\GitHub\medeval\.venv\Scripts\python.exe
# Valid:          True
```

### Multiple Environments

```bash
# List all environments
poetry env list

# Remove an environment
poetry env remove medeval-3.12

# Remove all environments
poetry env remove --all
```

### Activating Environment

**Option 1: Poetry Shell**
```bash
poetry shell
# Now you're in the virtual environment
python --version
medeval --help
exit  # to deactivate
```

**Option 2: Direct Activation (Windows)**
```powershell
.\.venv\Scripts\Activate.ps1
# Now you're in the virtual environment
deactivate  # to exit
```

**Option 3: Poetry Run (No activation needed)**
```bash
poetry run python script.py
poetry run medeval list-runs
```

---

## File Structure

```
medeval/
├── .venv/                    # Virtual environment (local, in .gitignore)
├── poetry.lock              # Locked dependency versions (in .gitignore)
├── pyproject.toml           # Poetry configuration & dependencies
├── poetry.ps1               # Helper script for Windows
├── requirements.txt         # Legacy pip requirements (for reference)
└── src/
    └── medeval/
        └── ...
```

---

## pyproject.toml Structure

```toml
[tool.poetry]
name = "medeval"
version = "0.1.0"
description = "A comprehensive evaluation framework for testing clinical AI systems"
authors = ["Taylor Quinn <taylorqquinn@users.noreply.github.com>"]

[tool.poetry.dependencies]
python = "^3.12"              # Requires Python 3.12+
pyyaml = ">=6.0"             # Core dependency
openai = {version = ">=1.0.0", optional = true}  # Optional

[tool.poetry.extras]
openai = ["openai"]           # Extra feature for OpenAI integration

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"            # Testing
pytest-cov = "^6.0.0"        # Coverage
flake8 = "^7.0.0"            # Linting

[tool.poetry.scripts]
medeval = "medeval.cli:main"  # CLI entry point
```

---

## Workflow Examples

### Daily Development

```bash
# 1. Pull latest code
git pull

# 2. Update dependencies if needed
.\poetry.ps1 update

# 3. Run tests
.\poetry.ps1 run pytest tests/unit -v

# 4. Make changes...

# 5. Test changes
.\poetry.ps1 run python tests\software\test_full_pipeline.py

# 6. Lint code
.\poetry.ps1 run flake8 src/medeval

# 7. Commit
git add .
git commit -m "Your changes"
```

### Adding a New Feature

```bash
# 1. Create feature branch
git checkout -b feature/new-evaluator

# 2. Add required packages
.\poetry.ps1 add scikit-learn

# 3. Implement feature...

# 4. Add tests...

# 5. Run tests
.\poetry.ps1 run pytest tests/unit -v

# 6. Commit
git add .
git commit -m "Add new evaluator"
```

### Setting Up on New Machine

```bash
# 1. Clone repository
git clone https://github.com/taylorqquinn/medeval.git
cd medeval

# 2. Install Poetry (if not installed)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# 3. Configure Poetry
poetry config virtualenvs.in-project true

# 4. Install dependencies
poetry install --extras openai

# 5. Verify installation
poetry run medeval --help
poetry run python tests\software\test_full_pipeline.py
```

---

## Troubleshooting

### Issue: "poetry: command not found"

**Solution:** Use full path or helper script
```bash
# Option 1: Use helper script
.\poetry.ps1 install

# Option 2: Use full path
C:\Users\Tay\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\Roaming\pypoetry\venv\Scripts\poetry.exe install

# Option 3: Add to PATH permanently
# Add this directory to your PATH environment variable:
# C:\Users\Tay\AppData\Roaming\Python\Scripts
```

### Issue: ".venv not in project directory"

**Solution:** Configure Poetry
```bash
poetry config virtualenvs.in-project true
poetry env remove --all
poetry install --extras openai
```

### Issue: "Wrong Python version"

**Solution:** Specify Python path
```bash
poetry env use "C:\Users\Tay\AppData\Local\Programs\Python\Python312\python.exe"
poetry install --extras openai
```

### Issue: "Lock file out of date"

**Solution:** Update lock file
```bash
poetry lock --no-update  # Just update lock file
# or
poetry lock              # Update lock file and dependencies
```

### Issue: "Cannot import medeval"

**Solution:** Use poetry run
```bash
# Don't do this:
python tests\software\test_full_pipeline.py

# Do this instead:
poetry run python tests\software\test_full_pipeline.py

# Or activate shell first:
poetry shell
python tests\software\test_full_pipeline.py
```

---

## Best Practices

1. **Always use Poetry for dependency management**
   ```bash
   # Good
   poetry add requests
   
   # Avoid
   pip install requests
   ```

2. **Keep lock file updated**
   ```bash
   # After adding/removing packages
   git add poetry.lock pyproject.toml
   git commit -m "Update dependencies"
   ```

3. **Use extras for optional features**
   ```bash
   # Only install what you need
   poetry install              # Core only
   poetry install --extras openai  # With OpenAI
   ```

4. **Run commands via Poetry**
   ```bash
   # Good
   poetry run pytest
   poetry run medeval list-runs
   
   # Avoid (unless in poetry shell)
   pytest
   medeval list-runs
   ```

5. **Document new dependencies**
   ```bash
   # Add comment in pyproject.toml explaining why
   requests = "^2.28"  # HTTP client for external API calls
   ```

---

## Summary

Poetry provides:
- ✅ Reproducible environments
- ✅ Dependency resolution
- ✅ Virtual environment management
- ✅ Development tools integration
- ✅ CLI script management

**Key Commands:**
- `.\poetry.ps1 install --extras openai` - Install everything
- `.\poetry.ps1 run medeval <command>` - Run CLI
- `.\poetry.ps1 run pytest tests/` - Run tests
- `.\poetry.ps1 add <package>` - Add dependency
- `.\poetry.ps1 update` - Update dependencies

For more information, see the [official Poetry documentation](https://python-poetry.org/docs/).
