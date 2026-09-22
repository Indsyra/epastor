# scripts/run_eval.py
import json
from db.session import SessionLocal
from db.models import Pastor
from sqlalchemy import select
from agent.graph import build_agent_graph

def run_eval(session, pastor_id: str, questions_path: str = "data/eval/questions.json"):
    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    agent = build_agent_graph(session)
    results = []

    for question in questions:
        print("=" * 80)
        print(f"Q: {question}")
        print("-" * 80)

        result = agent.invoke({
            "question": question,
            "pastor_id": pastor_id,
            "chunks": [],
            "answer": "",
            "books": [],
        })

        print(result["answer"])
        print()
        if result["books"]:
            print(f"📚 Livres trouvés : {[b['title'] for b in result['books']]}")
            print()

        results.append({
            "question": question,
            "answer": result["answer"],
            "books": result["books"],
        })

    with open("data/eval/results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n{len(results)} résultats sauvegardés dans data/eval/results.json")


if __name__ == "__main__":
    with SessionLocal() as session:
        pastor = session.scalars(select(Pastor).where(Pastor.display_name == "Mohammed Sanogo")).first()
        run_eval(session, pastor.id)