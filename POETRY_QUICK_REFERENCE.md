# Poetry Quick Reference for MedEval

## Using Poetry Commands

You have **three options** to run Poetry:

### Option 1: Use `poetry` directly (Recommended)
```powershell
# The alias is now in your PowerShell profile, so this works:
poetry env info
poetry run medeval list-runs
poetry install --extras openai
```

### Option 2: Use the helper script
```powershell
# If the alias isn't working, use the helper script:
.\poetry.ps1 env info
.\poetry.ps1 run medeval list-runs
.\poetry.ps1 install --extras openai
```

### Option 3: Use full path
```powershell
# Full path (not recommended, but always works):
C:\Users\Tay\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\Roaming\pypoetry\venv\Scripts\poetry.exe env info
```

---

## Most Common Commands

### Environment
```powershell
poetry env info          # Show environment details
poetry env list          # List all environments
poetry show              # List installed packages
poetry show --tree       # Show dependency tree
```

### Running MedEval
```powershell
poetry run medeval list-runs
poetry run medeval run --dataset datasets/clinical_cases.jsonl
poetry run medeval report --run <run_id>
poetry run medeval clean --keep 10
```

### Running Tests
```powershell
poetry run python tests\software\test_full_pipeline.py
poetry run pytest tests/unit -v
poetry run pytest tests/unit --cov=src/medeval
```

### Managing Dependencies
```powershell
poetry install                    # Install all dependencies
poetry install --extras openai    # Install with OpenAI
poetry add requests               # Add new package
poetry add --group dev black      # Add dev dependency
poetry remove requests            # Remove package
poetry update                     # Update all packages
poetry update openai              # Update specific package
```

### Shell Activation
```powershell
poetry shell                      # Activate virtual environment
# Now you can use medeval directly without "poetry run"
medeval list-runs
python tests\software\test_full_pipeline.py
exit                              # Deactivate
```

---

## Current Setup

✅ **Poetry Version:** 2.4.1  
✅ **Python Version:** 3.12.4  
✅ **Virtual Environment:** `C:\Users\Tay\Documents\GitHub\medeval\.venv`  
✅ **Packages Installed:** 27 (including OpenAI)  
✅ **Alias:** Set in PowerShell profile  

---

## Troubleshooting

### "poetry: command not found"
**Solution:**
```powershell
# Reload profile
. $PROFILE

# Or use helper script
.\poetry.ps1 <command>
```

### "Script execution disabled"
**Already fixed!** Execution policy set to RemoteSigned.

### "Module not found"
**Solution:** Always use `poetry run`:
```powershell
# Wrong
python script.py

# Right
poetry run python script.py
```

---

## Quick Test

```powershell
# Verify Poetry works
poetry env info

# Run MedEval
poetry run medeval list-runs

# Run tests
poetry run python tests\software\test_full_pipeline.py
```

---

## See Also

- `POETRY_GUIDE.md` - Comprehensive guide
- `POETRY_SETUP_COMPLETE.md` - Setup details
- `README.md` - Project overview
