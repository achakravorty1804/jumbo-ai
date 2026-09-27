import streamlit as st
import uuid
from memory.database import connect, add_chat_message, get_chat_history, list_conversations, get_user_by_slug
from agent.llm import complete, LLMError, usage_totals
from theme import apply_theme, top_banner

apply_theme()
st.markdown(
    """
    <style>
    [data-testid="stHeader"] {
        background: linear-gradient(100deg, #FFD400 0%, #FFDE33 45%, #FFE666 100%) !important;
        border-bottom: none !important;
        box-shadow: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# theme.py hides Streamlit's native sidebar nav (dashboard.py builds its own
# custom nav buttons instead) — this page wants to KEEP the native nav, just
# styled to match, so we undo just that one rule here.
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] {
        display: block !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNav"] a span,
    [data-testid="stSidebarNav"] a p {
        font-size: 16px !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: #FFD400 !important;
        border: 2px solid #E6C200 !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] span,
    [data-testid="stSidebarNav"] a[aria-current="page"] p {
        color: #0B1F3A !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <style>
    [data-testid="stChatMessage"] {
        max-width: 75%;
        margin-bottom: 10px;
    }
    /* User messages: pushed right, deep pink bubble */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        flex-direction: row-reverse;
        margin-left: auto;
        margin-right: 0;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
        background: #FF1493 !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 10px 16px !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] p {
        color: #FFFFFF !important;
    }

    /* Jumbo's replies: stay left, lighter pink bubble */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        margin-right: auto;
        margin-left: 0;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] {
        background: #FFD6E8 !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 10px 16px !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stChatMessageContent"] p {
        color: #0B1F3A !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <style>
    [data-testid="stBottom"],
    [data-testid="stBottomBlockContainer"] {
        background: linear-gradient(100deg, #FFD400 0%, #FFDE33 45%, #FFE666 100%) !important;
    }
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] div[data-baseweb="textarea"],
    [data-testid="stChatInput"] div[data-baseweb="base-input"] {
        background: #FF1493 !important;
        border-radius: 16px !important;
        border: none !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #FFFFFF !important;
        background: transparent !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #FFE1EC !important;
        opacity: 1 !important;
    }
    [data-testid="stChatInput"] button {
        background: #FFD400 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div style="
        margin-left: -2rem;
        margin-right: -2rem;
        margin-top: -1rem;
        width: calc(100% + 4rem);
        background: linear-gradient(100deg, #FFD400 0%, #FFDE33 45%, #FFE666 100%);
        padding: 26px 20px 22px 20px;
        margin-bottom: 14px;
        box-sizing: border-box;
        text-align: center;
    ">
        <div style="
            font-weight: 900;
            color: #0B1F3A;
            font-size: 32px;
            letter-spacing: 1px;
        ">🐘 ASK JUMBO</div>
        <div style="
            color: #0B1F3A;
            font-size: 14px;
            margin-top: 2px;
            opacity: 0.85;
        ">Ask me anything about today's news.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

MAX_CONTEXT_CHARS = 12000

try:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT headline, summary, created_at FROM stories ORDER BY id DESC LIMIT 30")
    rows = cur.fetchall()
except Exception as e:
    st.error(f"⚠️ Couldn't connect to Jumbo's memory (database): {e}")
    rows = []
    conn = None

def get_current_user():
    slug = st.query_params.get("user") or st.session_state.get("user_slug")

    if not slug:
        st.warning("🐘 Please open your personal Jumbo link to continue.")
        st.stop()

    if conn:
        user = get_user_by_slug(conn, slug)
        if user:
            st.query_params["user"] = slug
            return dict(user)

    st.warning("🐘 We couldn't recognize that link. Please check it and try again.")
    st.stop()

user = get_current_user()

if not rows:
    st.info("🐘 Jumbo doesn't have any stories in memory yet. Run a briefing first, then come back!")
    st.stop()

SUMMARY_CHAR_CAP = 300

context = ""
for h, s, c in rows:
    s_short = s if len(s) <= SUMMARY_CHAR_CAP else s[:SUMMARY_CHAR_CAP].rsplit(" ", 1)[0] + "..."
    line = f"- {h} ({c}): {s_short}\n"
    if len(context) + len(line) > MAX_CONTEXT_CHARS:
        break
    context += line

# --- Sidebar: conversation list, ChatGPT-style ---
conversations = list_conversations(conn, user["slug"]) if conn else []

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

chat_container = st.container(height=500)

for role, text in st.session_state.chat_history:
    label = user["name"] if role == "user" else "Jumbo"
    chat_container.chat_message(role).write(f"**{label}**\n\n{text}")

question = st.chat_input("Ask Jumbo about recent news...")
if question:
    conv_id = st.session_state.active_conversation
    chat_container.chat_message("user").write(f"**{user['name']}**\n\n{question}")
    st.session_state.chat_history.append(("user", question))
    if conn:
            add_chat_message(conn, conv_id, "user", question, user["slug"])

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

    chat_container.chat_message("assistant").write(f"**Jumbo**\n\n{answer}")
    st.session_state.chat_history.append(("assistant", answer))
    if conn:
            add_chat_message(conn, conv_id, "assistant", answer, user["slug"])
    st.rerun()

st.caption(
    f"Session usage — calls: {usage_totals['calls']}, "
    f"prompt tokens: {usage_totals['prompt_tokens']}, "
    f"completion tokens: {usage_totals['completion_tokens']}"
)