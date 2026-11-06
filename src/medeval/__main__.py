"""Entry point for running MedEval as a module.

This allows running MedEval via:
    python -m medeval <command> [args]
"""

from medeval.cli import main

if __name__ == '__main__':
    exit(main())
