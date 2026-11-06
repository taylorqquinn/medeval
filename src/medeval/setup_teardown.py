"""Setup and teardown utilities for MedEval test runs.

This module provides environment validation, cleanup, and reporting functionality
for the start and end of evaluation runs.
"""

import logging
import os
import shutil
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import yaml

logger = logging.getLogger('medeval.setup_teardown')


class SetupTeardownManager:
    """Manages setup and teardown phases for MedEval runs.
    
    Setup phase:
      - Validates environment (Python version, required packages, file paths)
      - Cleans old logs if configured
      - Creates necessary directories
      - Logs system information
    
    Teardown phase:
      - Creates summary reports
      - Archives artifacts if configured
      - Logs completion statistics
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the setup/teardown manager.
        
        Args:
            config: Configuration dictionary (typically from medeval_config.yaml).
        """
        self.config = config or {}
        self.setup_config = self.config.get('setup_teardown', {})
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def setup(self, log_dir: Path, artifacts_dir: Path) -> bool:
        """Perform setup phase.
        
        Args:
            log_dir: Base log directory.
            artifacts_dir: Artifacts directory for current run.
        
        Returns:
            True if setup successful, False otherwise.
        """
        if not self.setup_config.get('enable_setup', True):
            logger.info("Setup phase disabled in configuration")
            return True
        
        self.start_time = datetime.now()
        logger.info("="*60)
        logger.info("SETUP PHASE STARTED")
        logger.info("="*60)
        
        try:
            # Validate environment
            if self.setup_config.get('validate_environment', True):
                logger.info("Validating environment...")
                self._validate_environment()
                logger.info("Environment validation passed")
            
            # Clean old logs
            if self.setup_config.get('cleanup_old_logs', True):
                max_runs = self.setup_config.get('max_log_runs', 10)
                logger.info(f"Cleaning old logs (keeping {max_runs} most recent)...")
                self._cleanup_old_logs(log_dir, max_runs)
            
            # Log system information
            self._log_system_info()
            
            logger.info("="*60)
            logger.info("SETUP PHASE COMPLETED")
            logger.info("="*60)
            return True
            
        except Exception as e:
            logger.error(f"Setup phase failed: {e}", exc_info=True)
            return False
    
    def teardown(self, log_dir: Path, artifacts_dir: Path, 
                 result: Optional[Dict[str, Any]] = None) -> bool:
        """Perform teardown phase.
        
        Args:
            log_dir: Base log directory.
            artifacts_dir: Artifacts directory for current run.
            result: Optional evaluation result dictionary to include in summary.
        
        Returns:
            True if teardown successful, False otherwise.
        """
        if not self.setup_config.get('enable_teardown', True):
            logger.info("Teardown phase disabled in configuration")
            return True
        
        self.end_time = datetime.now()
        logger.info("="*60)
        logger.info("TEARDOWN PHASE STARTED")
        logger.info("="*60)
        
        try:
            # Create summary report
            if self.setup_config.get('create_summary', True):
                logger.info("Creating summary report...")
                self._create_summary(artifacts_dir, result)
            
            # Archive artifacts
            if self.setup_config.get('archive_artifacts', False):
                archive_format = self.setup_config.get('archive_format', 'zip')
                logger.info(f"Archiving artifacts as {archive_format}...")
                self._archive_artifacts(artifacts_dir, archive_format)
            
            # Log completion statistics
            self._log_completion_stats(result)
            
            logger.info("="*60)
            logger.info("TEARDOWN PHASE COMPLETED")
            logger.info("="*60)
            return True
            
        except Exception as e:
            logger.error(f"Teardown phase failed: {e}", exc_info=True)
            return False
    
    def _validate_environment(self):
        """Validate the runtime environment."""
        import sys
        
        logger.debug(f"Python version: {sys.version}")
        logger.debug(f"Python executable: {sys.executable}")
        
        # Check required packages
        required_packages = ['yaml']
        missing = []
        
        for package in required_packages:
            try:
                __import__(package)
                logger.debug(f"Package '{package}' found")
            except ImportError:
                missing.append(package)
                logger.warning(f"Package '{package}' not found")
        
        if missing:
            logger.warning(f"Missing packages: {', '.join(missing)}")
        
        # Check dataset and baseline paths
        dataset_config = self.config.get('dataset', {})
        default_dataset = dataset_config.get('default_path')
        default_baseline = dataset_config.get('default_baseline')
        
        if default_dataset and not os.path.exists(default_dataset):
            logger.warning(f"Default dataset not found: {default_dataset}")
        
        if default_baseline and not os.path.exists(default_baseline):
            logger.warning(f"Default baseline not found: {default_baseline}")
    
    def _cleanup_old_logs(self, log_dir: Path, keep_n: int):
        """Clean up old log runs, keeping only the N most recent.
        
        With the new structure, each run is in its own folder:
        .logs/medeval_YYYYMMDD_HHMMSS/
        
        Args:
            log_dir: The current run's directory (.logs/medeval_YYYYMMDD_HHMMSS/).
            keep_n: Number of recent runs to keep.
        """
        # Get the base .logs directory (parent of current run)
        base_log_dir = log_dir.parent
        
        if not base_log_dir.exists():
            logger.debug("No base log directory to clean")
            return
        
        # Get all run directories (medeval_*) sorted by modification time
        run_dirs = [d for d in base_log_dir.iterdir() 
                   if d.is_dir() and d.name.startswith('medeval_')]
        run_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove old runs (keeping keep_n most recent)
        removed_count = 0
        for old_dir in run_dirs[keep_n:]:
            try:
                logger.debug(f"Removing old run directory: {old_dir.name}")
                shutil.rmtree(old_dir, ignore_errors=True)
                removed_count += 1
            except Exception as e:
                logger.warning(f"Failed to remove {old_dir.name}: {e}")
        
        logger.info(f"Cleaned up {removed_count} old run(s)")
    
    def _log_system_info(self):
        """Log system and configuration information."""
        import sys
        import platform
        
        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"Python: {sys.version.split()[0]}")
        logger.info(f"Working Directory: {os.getcwd()}")
        
        exec_config = self.config.get('execution', {})
        mode = exec_config.get('mode', 'standard')
        logger.info(f"Execution Mode: {mode}")
    
    def _create_summary(self, artifacts_dir: Path, result: Optional[Dict[str, Any]]):
        """Create a summary report file.
        
        Args:
            artifacts_dir: Directory to save summary.
            result: Evaluation result dictionary.
        """
        summary_path = artifacts_dir / "run_summary.json"
        
        summary = {
            'run_id': artifacts_dir.name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None,
            'configuration': self.config.get('execution', {}),
        }
        
        if result:
            summary['result'] = {
                'passed': result.get('passed'),
                'num_cases': len(result.get('per_case_results', [])),
                'failures': result.get('failures', []),
                'key_metrics': {
                    k: v for k, v in result.get('aggregated', {}).items()
                    if isinstance(v, (int, float))
                }
            }
        
        with open(summary_path, 'w', encoding='utf-8') as fh:
            json.dump(summary, fh, indent=2)
        
        logger.info(f"Summary report saved to: {summary_path}")
    
    def _archive_artifacts(self, artifacts_dir: Path, format: str):
        """Archive artifacts directory.
        
        Args:
            artifacts_dir: Directory to archive.
            format: Archive format ('zip' or 'tar.gz').
        """
        archive_base = artifacts_dir.parent / f"{artifacts_dir.name}_archive"
        
        if format == 'zip':
            shutil.make_archive(str(archive_base), 'zip', str(artifacts_dir))
            logger.info(f"Artifacts archived to: {archive_base}.zip")
        elif format == 'tar.gz':
            shutil.make_archive(str(archive_base), 'gztar', str(artifacts_dir))
            logger.info(f"Artifacts archived to: {archive_base}.tar.gz")
        else:
            logger.warning(f"Unknown archive format: {format}")
    
    def _log_completion_stats(self, result: Optional[Dict[str, Any]]):
        """Log completion statistics.
        
        Args:
            result: Evaluation result dictionary.
        """
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            logger.info(f"Total execution time: {duration.total_seconds():.2f} seconds")
        
        if result:
            num_cases = len(result.get('per_case_results', []))
            passed = result.get('passed')
            logger.info(f"Evaluated {num_cases} case(s)")
            logger.info(f"Quality gate: {'PASSED' if passed else 'FAILED' if passed is False else 'N/A'}")
