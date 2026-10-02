import streamlit as st
import sys
from db.session import SessionLocal
from db.models import Pastor
from pathlib import Path
from sqlalchemy import select
from agent.graph import build_agent_graph

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

@st.cache_resource
def get_agent_and_pastors():
    session = SessionLocal()
    pastors = session.scalars(select(Pastor)).all()
    agent = build_agent_graph(session)
    return agent, session, pastors

agent, session, pastors = get_agent_and_pastors()

st.title("ePastor - Interface de test")

selected_pastor = st.selectbox(
    "Sélectionnez un pasteur",
    pastors,
    format_func=lambda pastor: pastor.display_name
)

question = st.text_input("Posez votre question au pasteur sélectionné")

if st.button("Envoyer"):
    with st.spinner("En cours de traitement..."):
        result = agent.invoke({
            "question": question,
            "pastor_id": selected_pastor.id,
            "chunks": [],
            "answer": "",
            "books": [],
        })
        
        st.markdown(
            f"**Réponse :** {result['answer']}\n\n\n"
        )

        if result['books']:
            st.markdown("**Livres trouvés :**")
            for book in result['books']:
                st.markdown(f"- [{book['title']}]({book['url']}) - {book['price']}")