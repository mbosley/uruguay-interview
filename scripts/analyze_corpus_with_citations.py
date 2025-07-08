#!/usr/bin/env python3
"""
Analyze interview corpus with hierarchical citations.
"""
import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db
from src.database.models import Interview, InterviewInsightCitation
from src.analysis.corpus_citation import CorpusAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_corpus():
    """Run corpus analysis with citation tracking."""
    
    # Load all interviews with annotations
    db = get_db()
    interviews = db.query(Interview).filter(
        Interview.annotation_json.isnot(None)
    ).all()
    
    logger.info(f"Analyzing corpus of {len(interviews)} interviews")
    
    # Convert to dicts with annotations
    interview_data = []
    for interview in interviews:
        data = {
            'id': interview.id,
            'metadata': {
                'location': interview.location,
                'municipality': interview.municipality,
                'department': interview.department,
                'date': interview.date.isoformat() if interview.date else None
            }
        }
        
        # Parse annotation
        if interview.annotation_json:
            try:
                annotation = json.loads(interview.annotation_json)
                data.update(annotation)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse annotation for interview {interview.id}")
                continue
            
        interview_data.append(data)
    
    # Run corpus analysis
    analyzer = CorpusAnalyzer(interview_data)
    corpus_report = analyzer.generate_corpus_report()
    
    # Save report
    output_path = Path('data/analysis/corpus_analysis_with_citations.json')
    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(corpus_report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Corpus analysis saved to {output_path}")
    
    # Generate citation visualization
    generate_citation_graph(corpus_report)
    
    # Print summary
    print_corpus_summary(corpus_report)
    
    return corpus_report

def generate_citation_graph(corpus_report: Dict):
    """Generate visualization of citation network."""
    try:
        import networkx as nx
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("NetworkX or matplotlib not installed. Skipping visualization.")
        return
    
    G = nx.DiGraph()
    
    # Add corpus insights as nodes
    for pattern_type, patterns in corpus_report['patterns'].items():
        for pattern in patterns:
            node_id = f"corpus_{pattern['insight_id']}"
            G.add_node(node_id, 
                      level='corpus',
                      type=pattern_type,
                      prevalence=pattern['prevalence'])
            
            # Add interview citations
            for cite in pattern['supporting_interviews'][:10]:  # Limit for visibility
                interview_node = f"interview_{cite['interview_id']}_{cite['insight_id']}"
                G.add_node(interview_node, level='interview')
                G.add_edge(interview_node, node_id, weight=cite['relevance_score'])
    
    # Layout and draw
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    plt.figure(figsize=(15, 10))
    
    # Draw nodes by level
    corpus_nodes = [n for n, d in G.nodes(data=True) if d['level'] == 'corpus']
    interview_nodes = [n for n, d in G.nodes(data=True) if d['level'] == 'interview']
    
    nx.draw_networkx_nodes(G, pos, corpus_nodes, node_color='red', 
                          node_size=500, label='Corpus Insights')
    nx.draw_networkx_nodes(G, pos, interview_nodes, node_color='blue',
                          node_size=200, label='Interview Insights')
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, alpha=0.5)
    
    plt.title("Citation Network: Corpus → Interview Insights")
    plt.legend()
    
    output_path = Path('data/analysis/citation_network.png')
    output_path.parent.mkdir(exist_ok=True, parents=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Citation network visualization saved to {output_path}")

def print_corpus_summary(corpus_report: Dict):
    """Print a summary of the corpus analysis."""
    print("\n" + "="*60)
    print("CORPUS ANALYSIS SUMMARY WITH CITATIONS")
    print("="*60)
    
    # Basic stats
    print(f"\nCorpus Size: {corpus_report['corpus_size']} interviews")
    print(f"Analysis Date: {corpus_report['analysis_timestamp']}")
    
    # Citation coverage
    citation_summary = corpus_report.get('citation_summary', {})
    print(f"\nCitation Coverage:")
    print(f"  Total Insights: {citation_summary.get('total_insights', 0)}")
    print(f"  Insights with Citations: {citation_summary.get('insights_with_citations', 0)}")
    print(f"  Coverage Rate: {citation_summary.get('citation_coverage', 0):.1%}")
    
    # Pattern summary
    print("\nPatterns Found:")
    for pattern_type, patterns in corpus_report['patterns'].items():
        print(f"\n{pattern_type.replace('_', ' ').title()}:")
        for i, pattern in enumerate(patterns[:5], 1):  # Top 5
            content = pattern['content']
            print(f"  {i}. {content.get('pattern', 'Unknown pattern')}")
            print(f"     - Prevalence: {pattern['prevalence']:.1%}")
            print(f"     - Confidence: {pattern['confidence']:.2f}")
            print(f"     - Supporting interviews: {len(pattern['supporting_interviews'])}")
            
            # Show regional variation if present
            if pattern.get('regional_variation'):
                top_region = max(pattern['regional_variation'].items(), 
                               key=lambda x: x[1])
                print(f"     - Highest in: {top_region[0]} ({top_region[1]:.1%})")
    
    print("\n" + "="*60)
    print("Analysis complete!")

if __name__ == "__main__":
    # Check if database exists
    db_path = Path('data/uruguay_interviews.db')
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        logger.info("Please run the annotation pipeline first to create the database")
        sys.exit(1)
    
    # Run analysis
    asyncio.run(analyze_corpus())