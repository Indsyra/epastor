import random
import json
from db.session import SessionLocal
from db.models import Pastor
from sqlalchemy import select
from db.queries import get_video_ids_with_chunks, get_chunk_window
from agent.prompts import build_question_generation_prompt
from agent.nodes import get_client  # le singleton client OpenAI, déjà écrit

def generate_eval_questions(session, pastor_id: str, n: int = 10) -> list[str]:
    """
    Generate n plausible questions from n distinct randomly selected videos for evaluation purposes.

    Args:
        session: The database session.
        pastor_id (str): The ID of the pastor whose videos are to be used.
        n (int): The number of questions to generate.

    Returns:
        list[str]: The generated questions.
    """
    # Get all video IDs with chunks for the given pastor
    video_ids = get_video_ids_with_chunks(session, pastor_id)
    if len(video_ids) < n:
        raise ValueError(f"Not enough videos with chunks to generate {n} questions.")

    selected_video_ids = random.sample(video_ids, n)
    questions = []
    client = get_client()

    for video_id in selected_video_ids:
        context = get_chunk_window(session, video_id)
        prompt = build_question_generation_prompt(context)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=prompt,
        )
        question = response.choices[0].message.content.strip()
        questions.append(question)

    return questions

if __name__ == "__main__":
    import os
    os.makedirs("data/eval", exist_ok=True)
    with SessionLocal() as session:
        pastor = session.scalars(select(Pastor).where(Pastor.display_name == "Mohammed Sanogo")).first()
        questions = generate_eval_questions(session, pastor.id, n=10)

        for q in questions:
            print(f"- {q}")

        with open("data/eval/questions.json", "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        print("\nQuestions generated and saved successfully to data/eval/questions.json")