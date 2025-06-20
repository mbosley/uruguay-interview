#!/usr/bin/env python3
"""
Add sample conversation text to make the chat interface more realistic.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_db
from src.database.models_enhanced import Interview, Turn

def add_sample_text():
    """Add sample conversation text to a few interviews."""
    print("📝 ADDING SAMPLE CONVERSATION TEXT")
    print("Making chat interface more realistic")
    print("=" * 50)
    
    db = get_db()
    
    # Sample conversation patterns
    interviewer_patterns = [
        "¿Cuáles considera que son las principales prioridades para el país?",
        "¿Puede contarme más sobre esa preocupación?",
        "¿Y a nivel local, qué problemas ve en su comunidad?",
        "¿Qué soluciones propone para estos problemas?",
        "¿Cómo ve el futuro de su comunidad?",
        "¿Hay algo más que le gustaría agregar?",
        "Muy interesante. ¿Puede dar un ejemplo específico?",
        "¿Cómo afecta esto a su vida diaria?",
        "¿Qué papel cree que debe jugar el gobierno?"
    ]
    
    participant_patterns = [
        "Bueno, yo creo que lo más importante es la educación y el empleo para los jóvenes.",
        "Sí, es un problema muy serio. En nuestra zona no hay suficientes oportunidades.",
        "Aquí en el interior nos sentimos un poco abandonados por las autoridades.",
        "Necesitamos más inversión en infraestructura y servicios públicos.",
        "La verdad, tengo esperanza pero también preocupación por el futuro.",
        "Me parece que deberían escuchar más a la gente de los pueblos.",
        "Por ejemplo, el transporte público es muy deficiente aquí.",
        "Afecta mucho, especialmente a las familias con niños pequeños.",
        "El gobierno debería estar más presente en el interior del país."
    ]
    
    with db.get_session() as session:
        # Get first few interviews with turns
        interviews = session.query(Interview).limit(5).all()
        
        updated_count = 0
        
        for interview in interviews:
            if interview.turns:
                print(f"Updating Interview {interview.interview_id}...")
                
                for i, turn in enumerate(sorted(interview.turns, key=lambda x: x.turn_id)):
                    # Determine speaker and assign realistic text
                    if turn.speaker == 'interviewer' or turn.turn_id % 2 == 1:
                        # Interviewer turn
                        pattern_idx = min(i // 2, len(interviewer_patterns) - 1)
                        turn.text = interviewer_patterns[pattern_idx]
                        turn.speaker = 'interviewer'
                    else:
                        # Participant turn
                        pattern_idx = min(i // 2, len(participant_patterns) - 1)
                        turn.text = participant_patterns[pattern_idx]
                        turn.speaker = 'participant'
                
                updated_count += 1
                print(f"  ✅ Updated {len(interview.turns)} turns")
        
        # Commit changes
        session.commit()
        
        print(f"\n📊 SAMPLE TEXT UPDATE SUMMARY")
        print("=" * 35)
        print(f"Interviews updated: {updated_count}")
        print("✅ Conversation text added successfully!")
        print("\n🎯 Now the chat interface will show realistic conversations")
        print("💬 Try: streamlit run src/dashboard/conversation_browser.py")
        
        return True


if __name__ == "__main__":
    success = add_sample_text()
    sys.exit(0 if success else 1)