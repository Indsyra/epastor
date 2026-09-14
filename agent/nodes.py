from typing import TypedDict
from db.models import Video
from sqlalchemy import select
from dotenv import load_dotenv
from agent.retrieval import search_chunks
import os
from openai import OpenAI
from agent.prompts import build_prompt, format_sources

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
_client = None

class AgentState(TypedDict):
    question: str
    pastor_id: str
    chunks: list[dict]
    answer: str

def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=openai_api_key)
    return _client

def make_retrieval_node(session):
    def retrieval_node(state: AgentState) -> AgentState:
        transcript_chunks = search_chunks(session, state["pastor_id"], state["question"])

        video_cache: dict[str, Video] = {}

        def get_video(video_id: str) -> Video:
            if video_id not in video_cache:
                video_cache[video_id] = session.get(Video, video_id)
            return video_cache[video_id]

        state["chunks"] = [
            {
                "text": chunk.text,
                "start_seconds": chunk.start_seconds,
                "end_seconds": chunk.end_seconds,
                "video_id": chunk.video_id,
                "video_title": get_video(chunk.video_id).title,
                "video_url": get_video(chunk.video_id).url,
            }
            for chunk in transcript_chunks
        ]
        return state

    return retrieval_node

def make_generation_node():
    def generation_node(state: AgentState) -> AgentState:
        messages = build_prompt(state["question"], state["chunks"])
        client = get_client()

        sources_text = format_sources(state["chunks"])
        state["answer"] = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        ).choices[0].message.content + "\n\n" + sources_text
        return state

    return generation_node
