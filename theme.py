"""Shared visual theme/CSS for all Jumbo pages."""

import streamlit as st

NAVY = "#0B1F3A"
NAVY_LIGHT = "#132A4D"
DEEP_PINK = "#FF1493"
PINK_DARK = "#C2185B"
PINK_MID = "#FF4FA0"
PINK_LIGHT = "#FFD6E8"
PINK_SOFT = "#FFE1EC"
PINK_BORDER = "#FFB6D5"
ACCENT_BLUE = "#CDEBFB"
WHITE = "#FFFFFF"
TEXT_DARK = "#3A3A3A"

SKY_PALE = "#EAF6FF"
SKY_LIGHT = "#CDEBFB"
SKY_MID = "#9FD8F5"

BG_PATTERN = (
    "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='140' height='140'%3E"
    "%3Cg fill='%23CDEBFB' fill-opacity='0.5'%3E"
    "%3Ccircle cx='20' cy='20' r='6'/%3E"
    "%3Ccircle cx='100' cy='60' r='4'/%3E"
    "%3Ccircle cx='60' cy='110' r='5'/%3E%3C/g%3E"
    "%3Cg fill='%239FD8F5' fill-opacity='0.35'%3E"
    "%3Ccircle cx='40' cy='80' r='3'/%3E"
    "%3Ccircle cx='110' cy='20' r='5'/%3E"
    "%3Ccircle cx='80' cy='130' r='4'/%3E%3C/g%3E"
    "%3C/svg%3E\")"
)

CUSTOM_CSS = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-color: {SKY_PALE};
    background-image: {BG_PATTERN};
    background-repeat: repeat;
}}

[data-testid="stHeader"] {{
    background: linear-gradient(100deg, {PINK_DARK} 0%, {DEEP_PINK} 45%, {PINK_MID} 100%);
}}

[data-testid="stSidebar"] {{
    background-color: {NAVY};
}}
[data-testid="stSidebar"] * {{
    color: {DEEP_PINK} !important;
}}
[data-testid="stSidebarNav"] a,
[data-testid="stSidebarNav"] a span,
[data-testid="stSidebarNav"] a p,
[data-testid="stSidebar"] a,
[data-testid="stSidebar"] a span,
[data-testid="stSidebar"] a p,
[data-testid="stSidebar"] li {{
    font-size: 24px !important;
    font-weight: 800 !important;
    text-transform: capitalize;
    padding: 6px 4px !important;
    border-radius: 10px;
}}
[data-testid="stSidebarNav"] a:hover,
[data-testid="stSidebar"] a:hover {{
    background-color: {NAVY_LIGHT} !important;
}}

[data-testid="stSidebarNav"] ul li:nth-child(2) {{
    display: none !important;
}}

[data-testid="stSidebar"] [data-testid="stPageLink"] a {{
    background-color: {PINK_LIGHT} !important;
    border: 2px solid {PINK_BORDER} !important;
    border-radius: 14px !important;
    justify-content: center !important;
    margin-top: 6px;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
    background-color: #FFC2DE !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"] p {{
    color: {NAVY} !important;
    font-weight: 800 !important;
    font-size: 16px !important;
}}

.block-container {{
    padding-top: 0rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
}}

div.stButton > button {{
    background-color: {PINK_LIGHT};
    border: 2px solid {PINK_BORDER};
    border-radius: 14px;
    padding: 12px 8px;
    font-size: 15px;
    font-weight: 700;
    color: {NAVY};
    transition: all 0.15s ease;
    width: 100%;
}}
div.stButton > button:hover {{
    border-color: {DEEP_PINK};
    background-color: #FFC2DE;
    color: {NAVY};
}}
div.stButton > button p {{
    font-size: 15px !important;
    white-space: pre-line;
    color: {NAVY} !important;
}}

.jumbo-postcard {{
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.jumbo-postcard:hover {{
    transform: translateY(-4px);
    box-shadow: 0 12px 26px rgba(11,31,58,0.20) !important;
}}

@keyframes jumboPopIn {{
    0% {{ opacity: 0; transform: scale(0.5); }}
    100% {{ opacity: 1; transform: scale(1); }}
}}
div[data-testid="stButton"] {{
    animation: jumboPopIn 0.35s ease forwards;
    opacity: 0;
}}
div[data-testid="stButton"]:nth-of-type(1) {{ animation-delay: 0.05s; }}
div[data-testid="stButton"]:nth-of-type(2) {{ animation-delay: 0.12s; }}
div[data-testid="stButton"]:nth-of-type(3) {{ animation-delay: 0.19s; }}
div[data-testid="stButton"]:nth-of-type(4) {{ animation-delay: 0.26s; }}
div[data-testid="stButton"]:nth-of-type(5) {{ animation-delay: 0.33s; }}
div[data-testid="stButton"]:nth-of-type(6) {{ animation-delay: 0.40s; }}
div[data-testid="stButton"]:nth-of-type(7) {{ animation-delay: 0.47s; }}
div[data-testid="stButton"]:nth-of-type(8) {{ animation-delay: 0.54s; }}
</style>
"""


def apply_theme():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_sidebar_brand():
    """Mascot image, a pink 'Ask Jumbo' button, and an Exit button
    in the navy sidebar, replacing the plain auto-generated nav link."""
    cols = st.sidebar.columns([1, 6, 1])
    with cols[1]:
        st.image("static/jumbo/jumbo_sidebar.png", use_container_width=True)

    st.sidebar.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)

    st.sidebar.page_link(
        "pages/ask_jumbo.py",
        label="🐘  Ask Jumbo",
        use_container_width=True,
    )

    st.sidebar.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    if st.sidebar.button("🚪  Exit", use_container_width=True, key="sidebar_exit"):
        st.session_state.stage = "goodbye"
        st.rerun()


def top_banner(fact):
    """Full-width pink gradient banner, centered text, aligned to the
    main content area (not the raw browser viewport, so it works
    correctly whether the sidebar is open or collapsed)."""
    st.markdown(
        f"""
        <div style="
            margin-left: -2rem;
            margin-right: -2rem;
            width: calc(100% + 4rem);
            background: linear-gradient(100deg, {PINK_DARK} 0%, {DEEP_PINK} 45%, {PINK_MID} 100%);
            padding: 28px 20px 24px 20px;
            margin-top: 0;
            margin-bottom: 18px;
            box-sizing: border-box;
            text-align: center;
        ">
            <div style="
                font-weight: 900;
                color: {WHITE};
                font-size: 32px;
                letter-spacing: 1px;
                text-shadow: 0 2px 6px rgba(0,0,0,0.15);
            ">🐘 JUMBO</div>
            <div style="
                color: {WHITE};
                font-size: 14px;
                margin-top: 2px;
                opacity: 0.9;
            ">Remembering what matters. Understanding what's happening.</div>
            <div style="
                color: {WHITE};
                font-size: 15px;
                margin-top: 14px;
                background: rgba(255,255,255,0.15);
                display: inline-block;
                padding: 8px 20px;
                border-radius: 20px;
            ">
                💡 <b>Did you know?</b> {fact}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )