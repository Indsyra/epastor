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

def build_book_extraction_prompt(answer: str) -> list[dict]:
    """
    Build messages to ask for book titles quoted in a given answer.

    Args:
        answer (str): The answer containing potential book titles.

    Returns:
        list[dict]: The messages to be sent to OpenAI for book extraction.
    """
    system_message = " ".join([
        "You extract book titles that the text presents as something",
        "the pastor actually teaches about or discusses.",
        "Do NOT extract a title if it only appears because the assistant",
        "is declining to answer, saying information is missing, or simply",
        "repeating a title that was asked about without discussing it.",
        "Respond ONLY with a JSON object of this exact shape:",
        '{"book_titles": ["title 1", "title 2"]}.',
        "If no book is genuinely discussed, respond with an empty list:",
        '{"book_titles": []}.',
        "Never invent a title that is not literally present in the text.",
    ])
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": answer},
    ]

def build_question_generation_prompt(context: str) -> list[dict]:
    """
    Build messages to ask the model to generate a plausible question
    that a visitor might ask, based on an excerpt from a sermon.

    Args:
        context (str): The excerpt from the sermon.

    Returns:
        list[dict]: The messages to be sent to OpenAI for question generation.
    """
    system_message = " ".join([
        "You are given an excerpt from a pastor's sermon.",
        "Generate ONE natural-language question, in the language of the excerpt, that a",
        "visitor might realistically ask, and that this excerpt would",
        "help answer.",
        "The question should sound like something a real person would",
        "type — not a summary of the excerpt, not a quiz question.",
        "Respond with ONLY the question, no preamble, no quotation marks.",
    ])

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": context},
    ]
