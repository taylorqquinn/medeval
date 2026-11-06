"""Logging configuration and utilities for MedEval.

This module provides centralized logging setup for the MedEval system, reading
configuration from medeval_config.yaml and setting up both console and file logging
with appropriate formatters and handlers.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import yaml


class MedEvalLogger:
    """Centralized logging manager for MedEval.
    
    Handles configuration loading, log directory creation, and logger setup
    with both console and rotating file handlers.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to ensure only one logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logger (only once due to singleton)."""
        if not self._initialized:
            self.config: Dict[str, Any] = {}
            self.log_dir: Optional[Path] = None
            self.artifacts_dir: Optional[Path] = None
            self.current_run_id: Optional[str] = None
            MedEvalLogger._initialized = True
    
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to config file. If None, searches for medeval_config.yaml
                        in the project root.
        
        Returns:
            Loaded configuration dictionary.
        """
        if config_path is None:
            # Try to find config in project root
            current_dir = Path(__file__).resolve()
            for parent in [current_dir] + list(current_dir.parents):
                candidate = parent / "medeval_config.yaml"
                if candidate.exists():
                    config_path = str(candidate)
                    break
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as fh:
                self.config = yaml.safe_load(fh) or {}
        else:
            # Default configuration if file not found
            self.config = self._default_config()
        
        return self.config
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration when config file is not found."""
        return {
            'logging': {
                'log_dir': '.logs',
                'log_file': 'medeval_{timestamp}.log',
                'console_level': 'INFO',
                'file_level': 'DEBUG',
                'format': '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
                'date_format': '%Y-%m-%d %H:%M:%S',
                'max_size_mb': 50,
                'backup_count': 5
            },
            'artifacts': {
                'artifacts_dir': 'artifacts',
                'save_predictions': True,
                'save_metrics': True,
                'save_quality_gate': True,
                'save_reports': True
            }
        }
    
    def setup_logging(self, config_path: Optional[str] = None, 
                      run_id: Optional[str] = None) -> logging.Logger:
        """Set up logging with console and file handlers.
        
        Args:
            config_path: Optional path to configuration file.
            run_id: Optional run identifier (default: timestamp).
        
        Returns:
            Configured root logger.
        """
        # Load configuration
        self.load_config(config_path)
        
        # Generate run ID
        self.current_run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create base log directory
        log_config = self.config.get('logging', {})
        log_base_dir_str = log_config.get('log_dir', '.logs')
        
        # Handle both absolute and relative paths for base directory
        if os.path.isabs(log_base_dir_str):
            log_base_dir = Path(log_base_dir_str)
        else:
            # Relative to project root
            project_root = self._find_project_root()
            log_base_dir = project_root / log_base_dir_str
        
        # Create run-specific directory: .logs/medeval_YYYYMMDD_HHMMSS/
        run_folder_name = f"medeval_{self.current_run_id}"
        self.log_dir = log_base_dir / run_folder_name
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs subdirectory: .logs/medeval_YYYYMMDD_HHMMSS/logs/
        logs_subdir = self.log_dir / "logs"
        logs_subdir.mkdir(parents=True, exist_ok=True)
        
        # Create artifacts subdirectory: .logs/medeval_YYYYMMDD_HHMMSS/artifacts/
        self.artifacts_dir = self.log_dir / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up root logger
        root_logger = logging.getLogger('medeval')
        root_logger.setLevel(logging.DEBUG)  # Capture everything, filter at handler level
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_level = getattr(logging, log_config.get('console_level', 'INFO').upper())
        console_handler.setLevel(console_level)
        
        # File handler with rotation - place in logs/ subdirectory
        log_filename = log_config.get('log_file', 'medeval_{timestamp}.log')
        log_filename = log_filename.replace('{timestamp}', self.current_run_id)
        log_filepath = logs_subdir / log_filename
        
        max_bytes = log_config.get('max_size_mb', 50) * 1024 * 1024
        backup_count = log_config.get('backup_count', 5)
        
        file_handler = logging.handlers.RotatingFileHandler(
            str(log_filepath),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_level = getattr(logging, log_config.get('file_level', 'DEBUG').upper())
        file_handler.setLevel(file_level)
        
        # Formatter
        log_format = log_config.get('format', '[%(asctime)s] %(name)s - %(levelname)s - %(message)s')
        date_format = log_config.get('date_format', '%Y-%m-%d %H:%M:%S')
        formatter = logging.Formatter(log_format, datefmt=date_format)
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # Log initialization
        root_logger.info("="*60)
        root_logger.info("MedEval Logging System Initialized")
        root_logger.info(f"Run ID: {self.current_run_id}")
        root_logger.info(f"Log Directory: {self.log_dir}")
        root_logger.info(f"Artifacts Directory: {self.artifacts_dir}")
        root_logger.info("="*60)
        
        return root_logger
    
    def _find_project_root(self) -> Path:
        """Find project root by looking for medeval_config.yaml or src/ directory."""
        current = Path(__file__).resolve()
        for parent in [current] + list(current.parents):
            if (parent / "medeval_config.yaml").exists() or (parent / "src").exists():
                return parent
        # Fallback to current working directory
        return Path.cwd()
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the given name under the medeval namespace.
        
        Args:
            name: Logger name (will be prefixed with 'medeval.').
        
        Returns:
            Configured logger instance.
        """
        return logging.getLogger(f'medeval.{name}')
    
    def get_artifacts_dir(self) -> Path:
        """Get the artifacts directory for the current run.
        
        Returns:
            Path to artifacts directory.
        """
        if self.artifacts_dir is None:
            raise RuntimeError("Logging not initialized. Call setup_logging() first.")
        return self.artifacts_dir
    
    def get_log_dir(self) -> Path:
        """Get the base log directory.
        
        Returns:
            Path to log directory.
        """
        if self.log_dir is None:
            raise RuntimeError("Logging not initialized. Call setup_logging() first.")
        return self.log_dir


# Global instance
_logger_manager = MedEvalLogger()


def setup_logging(config_path: Optional[str] = None, run_id: Optional[str] = None) -> logging.Logger:
    """Convenience function to set up logging.
    
    Args:
        config_path: Optional path to configuration file.
        run_id: Optional run identifier.
    
    Returns:
        Configured root logger.
    """
    return _logger_manager.setup_logging(config_path, run_id)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.
    
    Args:
        name: Logger name.
    
    Returns:
        Logger instance.
    """
    return _logger_manager.get_logger(name)


def get_artifacts_dir() -> Path:
    """Get the artifacts directory for the current run.
    
    Returns:
        Path to artifacts directory.
    """
    return _logger_manager.get_artifacts_dir()


def get_log_dir() -> Path:
    """Get the base log directory.
    
    Returns:
        Path to log directory.
    """
    return _logger_manager.get_log_dir()
