#!/usr/bin/env python3
"""
Command-line interface for annotation pipeline using configuration.
"""
import click
import logging
from pathlib import Path
from typing import Optional

from src.config.config_loader import get_config, reload_config
from src.pipeline.annotation.annotation_engine import AnnotationEngine
from src.pipeline.ingestion.document_processor import DocumentProcessor
from src.pipeline.full_pipeline import FullPipeline
from src.database.connection import init_database, get_db


@click.group()
@click.option('--config', '-c', help='Path to config.yaml file')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def cli(config: Optional[str], debug: bool):
    """Uruguay Interview Analysis CLI"""
    if config:
        # Load custom config file
        from src.config.config_loader import ConfigLoader
        loader = ConfigLoader(config_path=config)
        loader.load()
    
    # Set debug mode
    if debug:
        logging.basicConfig(level=logging.DEBUG)


@cli.command()
def info():
    """Show current configuration."""
    config = get_config()
    
    click.echo("Current Configuration:")
    click.echo(f"  AI Provider: {config.ai.provider}")
    click.echo(f"  AI Model: {config.ai.model}")
    click.echo(f"  Temperature: {config.ai.temperature}")
    click.echo(f"  Input Dir: {config.processing.input_dir}")
    click.echo(f"  Output Dir: {config.processing.output_dir}")
    click.echo(f"  Prompt File: {config.annotation.prompt_file}")
    click.echo(f"  Database: {config.database.name} @ {config.database.host}")
    click.echo(f"  Debug Mode: {config.debug}")


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--provider', '-p', help='Override AI provider')
@click.option('--model', '-m', help='Override AI model')
@click.option('--output', '-o', help='Output directory for annotations')
def annotate(file_path: str, provider: Optional[str], model: Optional[str], output: Optional[str]):
    """Annotate a single interview file."""
    config = get_config()
    
    # Initialize components
    processor = DocumentProcessor()
    engine = AnnotationEngine(
        model_provider=provider,  # Will use config if None
        model_name=model          # Will use config if None
    )
    
    # Process the file
    click.echo(f"Processing {file_path}...")
    interview = processor.process_interview(Path(file_path))
    
    # Show cost estimate
    costs = engine.calculate_annotation_cost(interview)
    provider_key = f"{engine.model_provider}_"
    for key, cost_data in costs.items():
        if key.startswith(provider_key):
            click.echo(f"Estimated cost: ${cost_data['total_cost']:.4f}")
            break
    
    # Annotate
    click.echo(f"Annotating with {engine.model_provider}/{engine.model_name}...")
    try:
        annotation, metadata = engine.annotate_interview(interview)
        
        # Save output
        output_dir = Path(output or config.processing.output_dir) / "annotations"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if config.annotation.save_xml:
            xml_path = output_dir / f"{interview.id}_annotation.xml"
            tree = ET.ElementTree(annotation)
            tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            click.echo(f"✓ Saved XML: {xml_path}")
        
        click.echo(f"✓ Annotation complete!")
        click.echo(f"  Processing time: {metadata['processing_time']:.2f}s")
        click.echo(f"  Confidence: {metadata.get('confidence', 'N/A')}")
        
    except Exception as e:
        click.echo(f"✗ Annotation failed: {e}", err=True)
        raise


@cli.command()
@click.option('--input-dir', '-i', help='Input directory (overrides config)')
@click.option('--output-dir', '-o', help='Output directory (overrides config)')
@click.option('--limit', '-l', type=int, help='Limit number of interviews to process')
@click.option('--provider', '-p', help='Override AI provider')
@click.option('--model', '-m', help='Override AI model')
def batch(input_dir: Optional[str], output_dir: Optional[str], limit: Optional[int], 
         provider: Optional[str], model: Optional[str]):
    """Process multiple interviews in batch."""
    config = get_config()
    
    # Use provided directories or config defaults
    input_path = Path(input_dir or config.processing.input_dir)
    output_path = Path(output_dir or config.processing.output_dir)
    
    # Find interview files
    patterns = [f"*.{fmt}" for fmt in config.processing.supported_formats]
    files = []
    for pattern in patterns:
        files.extend(input_path.glob(pattern))
    
    if limit:
        files = files[:limit]
    
    click.echo(f"Found {len(files)} interview files")
    
    if not files:
        click.echo("No files found to process", err=True)
        return
    
    # Initialize components
    processor = DocumentProcessor()
    engine = AnnotationEngine(
        model_provider=provider,
        model_name=model
    )
    
    # Calculate total cost estimate
    click.echo("Calculating cost estimate...")
    total_cost = 0
    for file in files[:3]:  # Sample first 3 files
        interview = processor.process_interview(file)
        costs = engine.calculate_annotation_cost(interview)
        provider_key = f"{engine.model_provider}_"
        for key, cost_data in costs.items():
            if key.startswith(provider_key):
                total_cost += cost_data['total_cost']
                break
    
    avg_cost = total_cost / min(3, len(files))
    estimated_total = avg_cost * len(files)
    
    click.echo(f"Estimated total cost: ${estimated_total:.2f}")
    
    # Check against budget
    if config.cost_management.daily_limit > 0:
        if estimated_total > config.cost_management.daily_limit:
            click.echo(f"⚠️  Warning: Estimated cost exceeds daily limit of ${config.cost_management.daily_limit}", err=True)
            if not click.confirm("Continue anyway?"):
                return
    
    # Process files
    click.echo(f"Processing {len(files)} interviews...")
    
    # Convert file list to InterviewDocument list
    interviews = []
    for file in files:
        try:
            interview = processor.process_interview(file)
            interviews.append(interview)
        except Exception as e:
            click.echo(f"Failed to process {file}: {e}", err=True)
    
    # Batch annotate
    results = engine.batch_annotate(
        interviews,
        output_dir=str(output_path / "annotations"),
        max_concurrent=config.ai.max_concurrent
    )
    
    # Summary
    success_count = sum(1 for _, success, _ in results if success)
    click.echo(f"\n✓ Batch processing complete: {success_count}/{len(results)} successful")


@cli.command()
@click.option('--provider', '-p', help='AI provider to check')
def costs(provider: Optional[str]):
    """Show cost comparison for different AI providers."""
    config = get_config()
    
    # Create a sample interview for cost calculation
    from src.pipeline.ingestion.document_processor import InterviewDocument
    sample = InterviewDocument(
        id="sample",
        date="2025-01-01",
        time="10:00",
        location="Montevideo",
        department=None,
        participant_count=3,
        text="Sample interview " * 500,  # ~500 words
        metadata={},
        file_path="sample.txt"
    )
    
    # Calculate costs for all providers
    engine = AnnotationEngine()  # Uses config default
    all_costs = engine.calculate_annotation_cost(sample)
    
    click.echo("Cost Comparison (per interview):")
    click.echo("-" * 50)
    
    # Group by provider
    providers = {}
    for key, cost_data in all_costs.items():
        provider_name = key.split('_')[0]
        if provider_name not in providers:
            providers[provider_name] = []
        providers[provider_name].append((key, cost_data))
    
    # Show costs
    for provider_name, models in providers.items():
        if provider and provider != provider_name:
            continue
            
        click.echo(f"\n{provider_name.upper()}:")
        for model_key, cost_data in sorted(models, key=lambda x: x[1]['total_cost']):
            click.echo(f"  {model_key}: ${cost_data['total_cost']:.6f}")
            if 'note' in cost_data:
                click.echo(f"    ({cost_data['note']})")
    
    # Project costs
    click.echo(f"\nProjected costs for 5,000 interviews:")
    click.echo("-" * 50)
    
    cheapest = min(all_costs.items(), key=lambda x: x[1]['total_cost'])
    click.echo(f"Cheapest option: {cheapest[0]} = ${cheapest[1]['total_cost'] * 5000:.2f}")
    
    if config.ai.provider in provider_name:
        current_key = None
        for key in all_costs:
            if key.startswith(config.ai.provider):
                current_key = key
                break
        
        if current_key:
            current_cost = all_costs[current_key]['total_cost'] * 5000
            click.echo(f"Current config: {current_key} = ${current_cost:.2f}")


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--save-db/--no-save-db', default=True, help='Save to database')
def pipeline(file_path: str, save_db: bool):
    """Process a single interview through the full pipeline."""
    pipeline = FullPipeline()
    
    click.echo(f"Processing {file_path} through full pipeline...")
    result = pipeline.process_interview(Path(file_path), save_to_db=save_db)
    
    if result['success']:
        click.echo(f"✓ Successfully processed interview {result['interview_id']}")
        click.echo(f"  Steps completed: {', '.join(result['steps_completed'])}")
        click.echo(f"  Total time: {result['total_time']:.2f}s")
        
        if 'extracted_data' in result:
            data = result['extracted_data']
            click.echo(f"  Sentiment: {data['sentiment']}")
            click.echo(f"  National priorities: {data['n_national_priorities']}")
            click.echo(f"  Local priorities: {data['n_local_priorities']}")
            click.echo(f"  Themes: {data['n_themes']}")
            confidence = data['confidence']
            if isinstance(confidence, (int, float)):
                click.echo(f"  Confidence: {confidence:.2f}")
            else:
                click.echo(f"  Confidence: {confidence}")
    else:
        click.echo(f"✗ Pipeline failed: {result['errors']}", err=True)


@cli.command()
@click.option('--input-dir', '-i', help='Input directory (overrides config)')
@click.option('--limit', '-l', type=int, help='Limit number of interviews')
@click.option('--save-db/--no-save-db', default=True, help='Save to database')
def pipeline_batch(input_dir: Optional[str], limit: Optional[int], save_db: bool):
    """Process multiple interviews through the full pipeline."""
    config = get_config()
    pipeline = FullPipeline()
    
    input_path = Path(input_dir or config.processing.input_dir)
    
    # Calculate cost estimate first
    click.echo("Calculating cost estimate...")
    cost_est = pipeline.calculate_batch_cost(input_path, limit)
    
    if 'error' in cost_est:
        click.echo(f"Error: {cost_est['error']}", err=True)
        return
    
    click.echo(f"Found {cost_est['total_files']} files")
    click.echo(f"Estimated cost: ${cost_est['estimated_total_cost']:.2f}")
    click.echo(f"Using: {cost_est['provider']}/{cost_est['model']}")
    
    # Check budget
    if config.cost_management.daily_limit > 0:
        if cost_est['estimated_total_cost'] > config.cost_management.daily_limit:
            click.echo(f"⚠️  Warning: Exceeds daily limit of ${config.cost_management.daily_limit}", err=True)
            if not click.confirm("Continue anyway?"):
                return
    
    # Process batch
    click.echo(f"\nProcessing batch...")
    results = pipeline.process_batch(input_path, limit=limit, save_to_db=save_db)
    
    # Show results
    click.echo(f"\n✓ Batch processing complete:")
    click.echo(f"  Successful: {results['successful']}/{results['total_files']}")
    click.echo(f"  Failed: {results['failed']}")
    click.echo(f"  Total time: {results['total_time']:.2f}s")
    click.echo(f"  Avg time per file: {results['avg_time_per_file']:.2f}s")
    
    if results['errors']:
        click.echo("\nErrors encountered:")
        for error in results['errors'][:5]:  # Show first 5 errors
            click.echo(f"  - {error['file']}: {error['errors']}")


@cli.command()
def init_db():
    """Initialize the database tables."""
    config = get_config()
    
    click.echo("Database Initialization")
    click.echo(f"Database: {config.database.name}")
    click.echo(f"Host: {config.database.host}:{config.database.port}")
    
    # Test connection
    db = get_db()
    if not db.test_connection():
        click.echo("✗ Failed to connect to database!", err=True)
        return
    
    click.echo("✓ Database connection successful")
    
    if click.confirm("Create all database tables?"):
        try:
            init_database()
            click.echo("✓ Database tables created successfully!")
        except Exception as e:
            click.echo(f"✗ Failed to initialize database: {e}", err=True)


@cli.command()
def db_status():
    """Check database connection and statistics."""
    from src.database.repository import InterviewRepository
    from src.database.connection import get_session
    
    config = get_config()
    
    # Test connection
    db = get_db()
    if not db.test_connection():
        click.echo("✗ Database connection failed!", err=True)
        return
    
    click.echo("✓ Database connection successful")
    
    # Get statistics
    try:
        db = get_db()
        with db.get_session() as session:
            repo = InterviewRepository(session)
            stats = repo.get_interview_statistics()
            
            click.echo(f"\nDatabase Statistics:")
            click.echo(f"  Total interviews: {stats['total_interviews']}")
            click.echo(f"  Completed: {stats['completed_interviews']}")
            click.echo(f"  Completion rate: {stats['completion_rate']:.1f}%")
            
            if stats['locations']:
                click.echo(f"\nInterviews by location:")
                for location, count in sorted(stats['locations'].items(), 
                                            key=lambda x: x[1], reverse=True):
                    click.echo(f"  - {location}: {count}")
    except Exception as e:
        click.echo(f"Error getting statistics: {e}", err=True)


if __name__ == "__main__":
    import xml.etree.ElementTree as ET
    cli()