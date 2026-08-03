import sys
from pathlib import Path

# Add project root to Python path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from database import SessionLocal
from agents.research_agent import ResearchAgent


def main():

    if len(sys.argv) < 2:
        print("Usage:")
        print("python scripts/run_pipeline.py <keyword>")
        return

    keyword = sys.argv[1]

    db = SessionLocal()

    try:
        agent = ResearchAgent(db)
        agent.research(keyword)
    finally:
        db.close()


if __name__ == "__main__":
    main()
