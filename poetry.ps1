# Poetry Helper Script for MedEval
# This script makes it easy to use Poetry commands without typing the full path

$poetry = "C:\Users\Tay\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\Roaming\pypoetry\venv\Scripts\poetry.exe"

# Check if poetry is available
if (!(Test-Path $poetry)) {
    Write-Host "Error: Poetry not found at $poetry" -ForegroundColor Red
    exit 1
}

# Show usage if no arguments
if ($args.Count -eq 0) {
    Write-Host @"

MedEval Poetry Helper
=====================

Usage: .\poetry.ps1 <command> [args...]

Common Commands:
  install          - Install dependencies
  update           - Update dependencies
  add <package>    - Add a new package
  remove <package> - Remove a package
  run <script>     - Run a script in the virtual environment
  shell            - Activate poetry shell
  env info         - Show environment info
  show             - List installed packages
  
Examples:
  .\poetry.ps1 install
  .\poetry.ps1 run python tests\software\test_full_pipeline.py
  .\poetry.ps1 run medeval list-runs
  .\poetry.ps1 add requests
  .\poetry.ps1 env info

"@ -ForegroundColor Cyan
    exit 0
}

# Execute the poetry command with all arguments
& $poetry $args
