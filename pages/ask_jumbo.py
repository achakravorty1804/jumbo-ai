import streamlit as st
import uuid
from memory.database import connect, add_chat_message, get_chat_history, list_conversations
from agent.llm import complete, LLMError, usage_totals

st.title("🐘 Ask Jumbo")

MAX_CONTEXT_CHARS = 6000

try:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT headline, summary, created_at FROM stories ORDER BY id DESC LIMIT 30")
    rows = cur.fetchall()
except Exception as e:
    st.error(f"⚠️ Couldn't connect to Jumbo's memory (database): {e}")
    rows = []
    conn = None

if not rows:
    st.info("🐘 Jumbo doesn't have any stories in memory yet. Run a briefing first, then come back!")
    st.stop()

context = ""
for h, s, c in rows:
    line = f"- {h} ({c}): {s}\n"
    if len(context) + len(line) > MAX_CONTEXT_CHARS:
        break
    context += line

# --- Sidebar: conversation list, ChatGPT-style ---
conversations = list_conversations(conn) if conn else []

with st.sidebar:
    st.subheader("🐘 Conversations")
    if st.button("➕ New chat", use_container_width=True):
        st.session_state.active_conversation = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.rerun()

    for convo in conversations:
        label = (convo["title"] or "New chat")[:40]
        if st.button(label, key=convo["conversation_id"], use_container_width=True):
            st.session_state.active_conversation = convo["conversation_id"]
            st.session_state.chat_history = get_chat_history(conn, convo["conversation_id"])
            st.rerun()

# First-ever visit: start a fresh conversation
if "active_conversation" not in st.session_state:
    st.session_state.active_conversation = str(uuid.uuid4())
    st.session_state.chat_history = []

for role, text in st.session_state.chat_history:
    st.chat_message(role).write(text)

question = st.chat_input("Ask Jumbo about recent news...")
if question:
    conv_id = st.session_state.active_conversation
    st.chat_message("user").write(question)
    st.session_state.chat_history.append(("user", question))
    if conn:
        add_chat_message(conn, conv_id, "user", question)

    system_prompt = (
        "You are Jumbo, a friendly elephant news assistant. Answer ONLY using the "
        "story context below. If the answer isn't in it, say you don't have that "
        "story yet. Keep answers short (2-4 sentences).\n\nSTORIES:\n" + context
    )
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": question}]

    with st.spinner("🐘 Jumbo is thinking..."):
        try:
            answer = complete(messages, max_tokens=300)
        except LLMError as e:
            answer = f"⚠️ Jumbo couldn't reach the brain right now ({e})."

    st.chat_message("assistant").write(answer)
    st.session_state.chat_history.append(("assistant", answer))
    if conn:
        add_chat_message(conn, conv_id, "assistant", answer)
    st.rerun()  # refresh sidebar so the new conversation's title appears

st.caption(
    f"Session usage — calls: {usage_totals['calls']}, "
    f"prompt tokens: {usage_totals['prompt_tokens']}, "
    f"completion tokens: {usage_totals['completion_tokens']}"
)