import yaml
from pathlib import Path

DEFAULT_CONFIG = {
    "database": {"path": "financial_data.db"},
    "logging": {"level": "INFO"},
    "data_settings": {"historical_period": "5y", "min_trading_days_for_sma": 200},
}


def load_config(config_path: str = "config.yaml"):
    """Load configuration from YAML file, fallback to defaults."""
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        # Merge with defaults
        merged = DEFAULT_CONFIG.copy()
        for k, v in config.items():
            if k in merged and isinstance(merged[k], dict):
                merged[k].update(v)
            else:
                merged[k] = v
        return merged
    return DEFAULT_CONFIG
