"""
Configuration loader for the Uruguay Interview Analysis project.
Loads configuration from YAML file and environment variables.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class AIConfig:
    """AI model configuration."""
    provider: str = "gemini"
    model: str = "gemini-2.0-flash"
    temperature: float = 0.3
    max_retries: int = 3
    batch_size: int = 10
    max_concurrent: int = 1


@dataclass
class ProcessingConfig:
    """Document processing configuration."""
    input_dir: str = "data/raw/interviews"
    output_dir: str = "data/processed"
    supported_formats: list = field(default_factory=lambda: ["txt", "docx", "odt"])
    encoding: str = "utf-8"
    min_interview_length: int = 100
    max_interview_length: int = 50000


@dataclass
class AnnotationConfig:
    """Annotation configuration."""
    prompt_version: str = "v1"
    prompt_file: str = "config/prompts/annotation_prompt_v1.xml"
    require_all_sections: bool = True
    min_confidence_score: float = 0.7
    save_xml: bool = True
    save_json: bool = True
    include_metadata: bool = True


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    name: str = "uruguay_interviews"
    user: str = "postgres"
    schema: str = "public"
    pool_size: int = 10
    echo: bool = False
    
    @property
    def url(self) -> str:
        """Get database URL, preferring environment variable."""
        return os.getenv(
            "DATABASE_URL",
            f"postgresql://{self.user}@{self.host}:{self.port}/{self.name}"
        )


@dataclass
class QualityConfig:
    """Quality control configuration."""
    min_annotation_completeness: float = 0.8
    flag_low_confidence: bool = True
    review_sample_rate: float = 0.1
    check_factual_consistency: bool = True
    cross_reference_responses: bool = True


@dataclass
class CostConfig:
    """Cost management configuration."""
    daily_limit: float = 10.0
    monthly_limit: float = 200.0
    prefer_cached_results: bool = True
    use_cheapest_model: bool = False
    alert_at_percentage: int = 80


@dataclass
class Config:
    """Main configuration container."""
    ai: AIConfig = field(default_factory=AIConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    annotation: AnnotationConfig = field(default_factory=AnnotationConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    cost_management: CostConfig = field(default_factory=CostConfig)
    
    # Additional settings
    log_level: str = "INFO"
    debug: bool = False
    test_mode: bool = False
    
    def __post_init__(self):
        """Set up logging after initialization."""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


class ConfigLoader:
    """Loads and manages configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader.
        
        Args:
            config_path: Path to YAML config file (defaults to project root config.yaml)
        """
        self.config_path = config_path or self._find_config_file()
        self._config_data: Dict[str, Any] = {}
        self._config: Optional[Config] = None
    
    def _find_config_file(self) -> Path:
        """Find config.yaml in project structure."""
        # Try multiple locations
        possible_paths = [
            Path("config.yaml"),
            Path("../config.yaml"),
            Path("../../config.yaml"),
            Path(__file__).parent.parent.parent / "config.yaml"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path.absolute()
        
        # Default to project root
        return Path(__file__).parent.parent.parent / "config.yaml"
    
    def load(self) -> Config:
        """Load configuration from file and environment."""
        if self._config is not None:
            return self._config
        
        # Load YAML file
        if self.config_path.exists():
            logger.info(f"Loading configuration from {self.config_path}")
            with open(self.config_path, 'r') as f:
                self._config_data = yaml.safe_load(f) or {}
        else:
            logger.warning(f"Config file not found at {self.config_path}, using defaults")
            self._config_data = {}
        
        # Create config objects
        self._config = Config(
            ai=self._load_ai_config(),
            processing=self._load_processing_config(),
            annotation=self._load_annotation_config(),
            database=self._load_database_config(),
            quality=self._load_quality_config(),
            cost_management=self._load_cost_config(),
            log_level=self._config_data.get("monitoring", {}).get("log_level", "INFO"),
            debug=self._config_data.get("development", {}).get("debug", False),
            test_mode=self._config_data.get("development", {}).get("test_mode", False)
        )
        
        return self._config
    
    def _load_ai_config(self) -> AIConfig:
        """Load AI configuration with environment overrides."""
        ai_data = self._config_data.get("ai", {})
        
        # Allow environment variables to override
        provider = os.getenv("AI_PROVIDER", ai_data.get("provider", "gemini"))
        model = os.getenv("AI_MODEL", ai_data.get("model", "gemini-2.0-flash"))
        
        return AIConfig(
            provider=provider,
            model=model,
            temperature=float(os.getenv("AI_TEMPERATURE", ai_data.get("temperature", 0.3))),
            max_retries=int(os.getenv("AI_MAX_RETRIES", ai_data.get("max_retries", 3))),
            batch_size=ai_data.get("batch_size", 10),
            max_concurrent=ai_data.get("max_concurrent", 1)
        )
    
    def _load_processing_config(self) -> ProcessingConfig:
        """Load processing configuration."""
        proc_data = self._config_data.get("processing", {})
        return ProcessingConfig(**proc_data)
    
    def _load_annotation_config(self) -> AnnotationConfig:
        """Load annotation configuration."""
        anno_data = self._config_data.get("annotation", {})
        return AnnotationConfig(**anno_data)
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration."""
        db_data = self._config_data.get("database", {})
        return DatabaseConfig(**db_data)
    
    def _load_quality_config(self) -> QualityConfig:
        """Load quality configuration."""
        quality_data = self._config_data.get("quality", {})
        return QualityConfig(**quality_data)
    
    def _load_cost_config(self) -> CostConfig:
        """Load cost management configuration."""
        cost_data = self._config_data.get("cost_management", {})
        return CostConfig(**cost_data)
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider from environment."""
        key_mapping = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "google": "GOOGLE_API_KEY"
        }
        
        env_var = key_mapping.get(provider.lower())
        if env_var:
            return os.getenv(env_var)
        return None
    
    def save(self, config: Config, path: Optional[str] = None) -> None:
        """Save configuration back to YAML file."""
        save_path = path or self.config_path
        
        # Convert to dict
        config_dict = {
            "ai": {
                "provider": config.ai.provider,
                "model": config.ai.model,
                "temperature": config.ai.temperature,
                "max_retries": config.ai.max_retries,
                "batch_size": config.ai.batch_size,
                "max_concurrent": config.ai.max_concurrent
            },
            "processing": {
                "input_dir": config.processing.input_dir,
                "output_dir": config.processing.output_dir,
                "supported_formats": config.processing.supported_formats,
                "encoding": config.processing.encoding,
                "min_interview_length": config.processing.min_interview_length,
                "max_interview_length": config.processing.max_interview_length
            },
            "annotation": {
                "prompt_version": config.annotation.prompt_version,
                "prompt_file": config.annotation.prompt_file,
                "require_all_sections": config.annotation.require_all_sections,
                "min_confidence_score": config.annotation.min_confidence_score,
                "save_xml": config.annotation.save_xml,
                "save_json": config.annotation.save_json,
                "include_metadata": config.annotation.include_metadata
            },
            "database": {
                "host": config.database.host,
                "port": config.database.port,
                "name": config.database.name,
                "user": config.database.user,
                "schema": config.database.schema,
                "pool_size": config.database.pool_size,
                "echo": config.database.echo
            },
            "quality": {
                "min_annotation_completeness": config.quality.min_annotation_completeness,
                "flag_low_confidence": config.quality.flag_low_confidence,
                "review_sample_rate": config.quality.review_sample_rate,
                "check_factual_consistency": config.quality.check_factual_consistency,
                "cross_reference_responses": config.quality.cross_reference_responses
            },
            "cost_management": {
                "daily_limit": config.cost_management.daily_limit,
                "monthly_limit": config.cost_management.monthly_limit,
                "prefer_cached_results": config.cost_management.prefer_cached_results,
                "use_cheapest_model": config.cost_management.use_cheapest_model,
                "alert_at_percentage": config.cost_management.alert_at_percentage
            },
            "monitoring": {
                "log_level": config.log_level
            },
            "development": {
                "debug": config.debug,
                "test_mode": config.test_mode
            }
        }
        
        with open(save_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Configuration saved to {save_path}")


# Singleton instance
_config_loader = ConfigLoader()
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = _config_loader.load()
    return _config


def reload_config() -> Config:
    """Force reload configuration from disk."""
    global _config
    _config = _config_loader.load()
    return _config


if __name__ == "__main__":
    # Test configuration loading
    config = get_config()
    print(f"AI Provider: {config.ai.provider}")
    print(f"AI Model: {config.ai.model}")
    print(f"Database URL: {config.database.url}")
    print(f"Debug Mode: {config.debug}")