def build_prompt(question: str, chunks: list[dict]) -> list[dict]:
    """
    Build messages for OpenAI call, based on the question and retrieved chunks.

    Args:
        question (str): The user's question.
        chunks (list[dict]): The retrieved transcript chunks.

    Returns:
        list[dict]: The messages to be sent to OpenAI.
    """

    system_message = (
        "You are an assistant that answers questions based "
        "only on the provided transcript chunks below. "
        "If the chunks do not allow you to answer the "
        "question, explicitly tell the user rather than "
        "attempting to guess an answer. Do not quote "
        "an information not contained in the provided chunks. "
        "Always answer in the same language as the question, "
        "Even if the chunks are in a different language. "
        "After each claim drawn from a source, cite its number "
        "in brackets, like [1] or [2], right after the sentence."
    )

    sources_text = "\n\n".join([f"[{i}] {chunk['text']}" for i, chunk in enumerate(chunks, start=1)])
    user_message = f"Available extractions:\n{sources_text}\n\nQuestion: {question}"

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]

def format_sources(chunks: list[dict]) -> str:
    """
    Format the retrieved transcript chunks as a string with numbered sources.

    Args:
        chunks (list[dict]): The retrieved transcript chunks.

    Returns:
        str: The formatted sources videos urls.
    """

    return "Sources:\n" + "\n".join([f"[{i}] {chunk['video_title']} (at {int(chunk['start_seconds'] // 60)}:{int(chunk['start_seconds'] % 60):02d}) - {chunk['video_url']}&t={int(chunk['start_seconds'])}s" for i, chunk in enumerate(chunks, start=1)])