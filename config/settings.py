"""
Central configuration management for Uruguay Active Listening project.
"""
import os
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"

# Data directories
RAW_DATA_DIR = DATA_DIR / "raw" / "interviews"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
TEXT_INTERVIEWS_DIR = PROCESSED_DATA_DIR / "interviews_txt"
ANNOTATIONS_DIR = PROCESSED_DATA_DIR / "annotations"
EXTRACTED_DATA_DIR = PROCESSED_DATA_DIR / "extracted"
CACHE_DIR = DATA_DIR / "cache"
EXPORTS_DIR = DATA_DIR / "exports"

# Config paths
PROMPTS_DIR = CONFIG_DIR / "prompts"
DATABASE_CONFIG_DIR = CONFIG_DIR / "database"
DASHBOARD_CONFIG_DIR = CONFIG_DIR / "dashboards"

@dataclass
class APIConfig:
    """API configuration for external services."""
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    whatsapp_api_key: str = os.environ.get("WHATSAPP_API_KEY", "")
    whatsapp_phone_id: str = os.environ.get("WHATSAPP_PHONE_ID", "")

@dataclass
class PipelineConfig:
    """Configuration for the annotation pipeline."""
    batch_size: int = 10
    max_workers: int = 4
    confidence_threshold: float = 0.85
    require_human_review_below: float = 0.70
    max_retries: int = 3
    timeout_seconds: int = 300

@dataclass
class QualityConfig:
    """Configuration for quality assurance."""
    min_confidence_score: float = 0.80
    hallucination_detection_enabled: bool = True
    cross_validation_sample_rate: float = 0.10  # 10% of interviews
    human_review_sample_rate: float = 0.05  # 5% of interviews
    consistency_check_enabled: bool = True

@dataclass
class DashboardConfig:
    """Configuration for dashboard generation."""
    update_frequency_hours: int = 24
    cache_duration_hours: int = 6
    default_date_range_days: int = 30
    enable_real_time_updates: bool = True

@dataclass
class ResearchConfig:
    """Configuration for research components."""
    digital_twin_min_interviews: int = 3  # Min interviews per participant
    synthetic_survey_sample_size: int = 1000
    reasoning_trace_depth: int = 5  # Levels of reasoning to extract

class Config:
    """Main configuration class."""
    
    # Default file names
    DEFAULT_ANNOTATION_PROMPT = "annotation_prompt_v1.xml"
    DEFAULT_FOLLOWUP_PROMPT = "followup_prompts.yaml"
    
    def __init__(self):
        self.api = APIConfig()
        self.pipeline = PipelineConfig()
        self.quality = QualityConfig()
        self.dashboard = DashboardConfig()
        self.research = ResearchConfig()
        
        # Create necessary directories
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            RAW_DATA_DIR,
            TEXT_INTERVIEWS_DIR,
            ANNOTATIONS_DIR,
            EXTRACTED_DATA_DIR,
            CACHE_DIR,
            EXPORTS_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_prompt_path(self, prompt_name: str) -> Path:
        """Get the full path to a prompt file."""
        return PROMPTS_DIR / prompt_name
    
    def get_database_schema_path(self, schema_name: str) -> Path:
        """Get the full path to a database schema file."""
        return DATABASE_CONFIG_DIR / schema_name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "api": self.api.__dict__,
            "pipeline": self.pipeline.__dict__,
            "quality": self.quality.__dict__,
            "dashboard": self.dashboard.__dict__,
            "research": self.research.__dict__,
        }

# Global configuration instance
config = Config()