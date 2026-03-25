import json
import os
from typing import Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv
import logging

class ConfigManager:
    def __init__(self, config_file: str = "config.json", env_file: str = ".env"):
        self.config_file = Path(config_file)
        self.env_file = Path(env_file)
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        if self.env_file.exists():
            load_dotenv(self.env_file)
        
        # Load configuration
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        # Default configuration
        default_config = {
            "monitored_channels": ["#general", "#random"],
            "analysis_days": 7,
            "burnout_threshold": -0.3,
            "min_messages_per_day": 5,
            "sentiment_threshold": {
                "positive": 0.1,
                "negative": -0.1
            },
            "engagement_drop_threshold": 0.5,
            "consecutive_negative_days": 3,
            "rate_limit_delay": 1,
            "database": {
                "path": "./data/engagement.db",
                "retention_days": 30
            },
            "reports": {
                "directory": "./reports",
                "formats": ["json", "html"],
                "auto_cleanup_days": 90
            },
            "logging": {
                "level": "INFO",
                "file": "./logs/engagement.log"
            }
        }
        
        # Load from JSON file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    # Merge with defaults
                    config = self.merge_configs(default_config, file_config)
            except Exception as e:
                self.logger.warning(f"Failed to load config file: {e}. Using defaults.")
                config = default_config
        else:
            config = default_config
        
        # Override with environment variables
        config = self.apply_env_overrides(config)
        
        # Validate configuration
        self.validate_config(config)
        
        return config
    
    def merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Environment variable mappings
        env_mappings = {
            'SLACK_BOT_TOKEN': lambda c: c,  # Special case - not stored in config
            'DATABASE_PATH': lambda c: self.set_nested_value(c, 'database.path', os.getenv('DATABASE_PATH')),
            'REPORTS_DIR': lambda c: self.set_nested_value(c, 'reports.directory', os.getenv('REPORTS_DIR')),
            'ANALYSIS_DAYS': lambda c: self.set_nested_value(c, 'analysis_days', int(os.getenv('ANALYSIS_DAYS', c['analysis_days']))),
            'BURNOUT_THRESHOLD': lambda c: self.set_nested_value(c, 'burnout_threshold', float(os.getenv('BURNOUT_THRESHOLD', c['burnout_threshold']))),
            'RATE_LIMIT_DELAY': lambda c: self.set_nested_value(c, 'rate_limit_delay', float(os.getenv('RATE_LIMIT_DELAY', c['rate_limit_delay']))),
            'LOG_LEVEL': lambda c: self.set_nested_value(c, 'logging.level', os.getenv('LOG_LEVEL', c['logging']['level'])),
            'MONITORED_CHANNELS': lambda c: self.set_nested_value(c, 'monitored_channels', 
                                                                os.getenv('MONITORED_CHANNELS', ','.join(c['monitored_channels'])).split(','))
        }
        
        for env_var, setter in env_mappings.items():
            if env_var in os.environ:
                try:
                    config = setter(config)
                except Exception as e:
                    self.logger.warning(f"Failed to apply environment override for {env_var}: {e}")
        
        return config
    
    def set_nested_value(self, config: Dict[str, Any], path: str, value: Any) -> Dict[str, Any]:
        keys = path.split('.')
        current = config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
        return config
    
    def validate_config(self, config: Dict[str, Any]):
        # Validate required settings
        if not config.get('monitored_channels'):
            raise ValueError("At least one monitored channel must be specified")
        
        if config.get('analysis_days', 0) < 1:
            raise ValueError("Analysis days must be at least 1")
        
        if not -1.0 <= config.get('burnout_threshold', 0) <= 1.0:
            raise ValueError("Burnout threshold must be between -1.0 and 1.0")
        
        if config.get('rate_limit_delay', 0) < 0:
            raise ValueError("Rate limit delay cannot be negative")
        
        # Validate Slack token exists
        if not self.get_slack_token():
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")
        
        # Create directories
        os.makedirs(Path(config['database']['path']).parent, exist_ok=True)
        os.makedirs(config['reports']['directory'], exist_ok=True)
        
        if 'file' in config['logging']:
            os.makedirs(Path(config['logging']['file']).parent, exist_ok=True)
    
    def get_slack_token(self) -> str:
        token = os.getenv('SLACK_BOT_TOKEN')
        if not token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")
        return token
    
    def get_monitored_channels(self) -> List[str]:
        return self.config['monitored_channels']
    
    def get_analysis_days(self) -> int:
        return self.config['analysis_days']
    
    def get_burnout_threshold(self) -> float:
        return self.config['burnout_threshold']
    
    def get_consecutive_negative_days(self) -> int:
        return self.config['consecutive_negative_days']
    
    def get_engagement_drop_threshold(self) -> float:
        return self.config['engagement_drop_threshold']
    
    def get_rate_limit_delay(self) -> float:
        return self.config['rate_limit_delay']
    
    def get_database_path(self) -> str:
        return self.config['database']['path']
    
    def get_database_retention_days(self) -> int:
        return self.config['database']['retention_days']
    
    def get_reports_directory(self) -> str:
        return self.config['reports']['directory']
    
    def get_report_formats(self) -> List[str]:
        return self.config['reports']['formats']
    
    def get_logging_config(self) -> Dict[str, Any]:
        return self.config['logging']
    
    def get_min_messages_per_day(self) -> int:
        return self.config['min_messages_per_day']
    
    def get_sentiment_thresholds(self) -> Dict[str, float]:
        return self.config['sentiment_threshold']
    
    def save_config(self, config_path: str = None):
        path = Path(config_path) if config_path else self.config_file
        
        # Remove sensitive data before saving
        safe_config = self.config.copy()
        
        try:
            with open(path, 'w') as f:
                json.dump(safe_config, f, indent=2)
            self.logger.info(f"Configuration saved to {path}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def update_config(self, updates: Dict[str, Any]):
        self.config = self.merge_configs(self.config, updates)
        self.validate_config(self.config)
        self.logger.info("Configuration updated")
    
    def get_full_config(self) -> Dict[str, Any]:
        return self.config.copy()