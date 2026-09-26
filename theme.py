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

YELLOW = "#FFD400"
YELLOW_BORDER = "#E6C200"

FACT_BUBBLE_BG = "#DFF6E0"
FACT_BUBBLE_BORDER = "#8FD99B"
FACT_BUBBLE_TEXT = "#1F4B24"
FACT_HEADING_COLOR = "#1B7A3D"

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
[data-stale="true"] {{
    display: none !important;
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

[data-testid="stSidebarNav"] {{
    display: none !important;
}}

[data-testid="stSidebar"] [data-testid="stPageLink"] a {{
    background-color: {YELLOW} !important;
    border: 2px solid {YELLOW_BORDER} !important;
    border-radius: 14px !important;
    justify-content: center !important;
    margin-top: 6px;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
    background-color: #FFE04D !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"] p {{
    color: {NAVY} !important;
    font-weight: 800 !important;
    font-size: 16px !important;
}}

[data-testid="stSidebar"] button[kind="primary"] {{
    background-color: {DEEP_PINK} !important;
    border: 2px solid {DEEP_PINK} !important;
}}
[data-testid="stSidebar"] button[kind="primary"] p {{
    color: {NAVY} !important;
    font-weight: 800 !important;
}}
[data-testid="stSidebar"] button[kind="primary"]:hover {{
    background-color: {PINK_DARK} !important;
    border-color: {PINK_DARK} !important;
}}

.block-container {{
    padding-top: 1rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-bottom: 0.5rem !important;
    max-width: 100% !important;
}}

[data-testid="stVerticalBlock"] {{
    gap: 0.6rem !important;
}}
[data-testid="stHorizontalBlock"] {{
    gap: 0.6rem !important;
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

/* Category picker buttons only — same footprint as before, just
   bigger/bolder TEXT (not a bigger box), so nothing shifts down
   into the fixed-position fact bubble in the corner. */
div[class*="st-key-ring_"] button {{
    background: linear-gradient(145deg, {PINK_LIGHT} 0%, #FFC2DE 100%) !important;
    border: 2px solid {DEEP_PINK} !important;
    border-radius: 14px !important;
    padding: 12px 8px !important;
    box-shadow: 0 4px 10px rgba(255,20,147,0.18) !important;
    transition: all 0.15s ease !important;
}}
div[class*="st-key-ring_"] button p {{
    font-size: 17px !important;
    font-weight: 800 !important;
    line-height: 1.4 !important;
    color: {NAVY} !important;
    white-space: pre-line !important;
}}
div[class*="st-key-ring_"] button:hover {{
    background: linear-gradient(145deg, #FFC2DE 0%, {PINK_LIGHT} 100%) !important;
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(255,20,147,0.28) !important;
}}

.st-key-fact_bubble_container {{
    position: fixed;
    bottom: 18px;
    right: 18px;
    max-width: 250px;
    z-index: 9999;
}}
.st-key-fact_bubble_container div[data-testid="stButton"] > button {{
    background: transparent !important;
    border: none !important;
    color: {FACT_HEADING_COLOR} !important;
    font-weight: 900 !important;
    font-size: 16px !important;
    padding: 0 !important;
    min-height: 0 !important;
    height: 22px !important;
    width: 100% !important;
    box-shadow: none !important;
    line-height: 1 !important;
}}
.st-key-fact_bubble_container div[data-testid="stButton"] > button:hover {{
    color: {DEEP_PINK} !important;
    background: transparent !important;
}}
.st-key-fact_bubble_container div[data-testid="stButton"] > button p {{
    color: inherit !important;
    font-size: 16px !important;
}}
.st-key-fact_bubble_container div[data-testid="element-container"] {{
    animation: none !important;
    opacity: 1 !important;
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
.st-key-story_tile_stack {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 18px;
    max-width: 640px;
    margin: 0 auto;
}}

.st-key-story_tile_stack div.stButton > button {{
    min-height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}}

@keyframes tileFlipIn {{
    0% {{ opacity: 0; transform: perspective(600px) rotateX(-90deg); }}
    100% {{ opacity: 1; transform: perspective(600px) rotateX(0deg); }}
}}

.st-key-story_tile_stack div[data-testid="stButton"] {{
    animation: tileFlipIn 0.6s ease forwards;
    opacity: 0;
    transform-origin: center top;
}}

.st-key-story_tile_stack div[data-testid="stButton"]:nth-of-type(1)  {{ animation-delay: 0.20s; }}
.st-key-story_tile_stack div[data-testid="stButton"]:nth-of-type(2)  {{ animation-delay: 0.80s; }}
.st-key-story_tile_stack div[data-testid="stButton"]:nth-of-type(3)  {{ animation-delay: 1.40s; }}
.st-key-story_tile_stack div[data-testid="stButton"]:nth-of-type(4)  {{ animation-delay: 2.00s; }}
.st-key-story_tile_stack div[data-testid="stButton"]:nth-of-type(5)  {{ animation-delay: 2.60s; }}
.st-key-story_tile_stack div[data-testid="stButton"]:nth-of-type(6)  {{ animation-delay: 3.20s; }}
.st-key-story_tile_stack div[data-testid="stButton"]:nth-of-type(7)  {{ animation-delay: 3.80s; }}
.st-key-story_tile_stack div[data-testid="stButton"]:nth-of-type(8)  {{ animation-delay: 4.40s; }}
.st-key-story_tile_stack div[data-testid="stButton"]:nth-of-type(9)  {{ animation-delay: 5.00s; }}
.st-key-story_tile_stack div[data-testid="stButton"]:nth-of-type(10) {{ animation-delay: 5.60s; }}
.st-key-story_tile_stack div[data-testid="stButton"]:nth-of-type(11) {{ animation-delay: 6.20s; }}
.st-key-story_tile_stack [class*="st-key-tile_wrap_"] {{
    animation: tileFlipIn 0.6s ease forwards;
    opacity: 0;
    transform-origin: center top;
}}

.st-key-tile_wrap_card_0  {{ animation-delay: 0.20s; }}
.st-key-tile_wrap_card_1  {{ animation-delay: 0.80s; }}
.st-key-tile_wrap_card_2  {{ animation-delay: 1.40s; }}
.st-key-tile_wrap_card_3  {{ animation-delay: 2.00s; }}
.st-key-tile_wrap_card_4  {{ animation-delay: 2.60s; }}
.st-key-tile_wrap_card_5  {{ animation-delay: 3.20s; }}
.st-key-tile_wrap_card_6  {{ animation-delay: 3.80s; }}
.st-key-tile_wrap_card_7  {{ animation-delay: 4.40s; }}
.st-key-tile_wrap_card_8  {{ animation-delay: 5.00s; }}
.st-key-tile_wrap_card_9  {{ animation-delay: 5.60s; }}
.st-key-tile_wrap_card_10 {{ animation-delay: 6.20s; }}
.st-key-tile_wrap_card_11 {{ animation-delay: 6.80s; }}

.st-key-back_to_home div[data-testid="stButton"] > button,
.st-key-back_to_category div[data-testid="stButton"] > button {{
    background: #FFF3B0 !important;
    border: 2px solid #E6C200 !important;
    color: {NAVY} !important;
    font-weight: 700 !important;
    font-family: 'Trebuchet MS', 'Segoe UI', sans-serif !important;
    letter-spacing: 0.5px !important;
}}
.st-key-back_to_home div[data-testid="stButton"] > button:hover,
.st-key-back_to_category div[data-testid="stButton"] > button:hover {{
    background: #FFE066 !important;
}}

/* ============ About Us / Contact Info redesign (compact, no-scroll) ============ */

.jumbo-info-card {{
    background: {WHITE};
    border: 2px solid {PINK_BORDER};
    border-radius: 20px;
    padding: 8px 18px;
    box-shadow: 0 10px 24px rgba(11,31,58,0.10);
    margin-top: 2px;
}}
.jumbo-card-title {{
    font-size: 15px;
    font-weight: 800;
    color: {NAVY};
    margin-bottom: 6px;
    font-family: 'Trebuchet MS', 'Segoe UI', sans-serif;
}}
.jumbo-item {{
    background: {PINK_SOFT};
    border-left: 5px solid {DEEP_PINK};
    border-radius: 10px;
    padding: 8px 14px;
    margin-bottom: 8px;
}}
.jumbo-item b {{ color: {PINK_DARK}; font-size: 14px; }}
.jumbo-item span {{ color: {TEXT_DARK}; font-size: 12.5px; line-height: 1.3; }}
.jumbo-big-text {{
    font-size: 19px;
    font-weight: 700;
    color: {NAVY};
    line-height: 1.5;
}}
.jumbo-highlight {{
    background: linear-gradient(90deg, {PINK_LIGHT} 0%, {ACCENT_BLUE} 100%);
    border-radius: 14px;
    padding: 14px 18px;
    text-align: center;
    font-weight: 800;
    color: {NAVY};
    font-size: 15px;
    margin: 16px 0;
}}
.jumbo-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-top: 8px;
}}
.jumbo-grid > div {{
    background: {SKY_PALE};
    border: 2px solid {SKY_MID};
    border-radius: 16px;
    padding: 18px 14px;
    text-align: center;
    font-size: 26px;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.jumbo-grid > div:hover {{
    transform: translateY(-4px);
    box-shadow: 0 10px 20px rgba(11,31,58,0.15);
}}
.jumbo-grid > div b {{ display: block; font-size: 15px; color: {NAVY}; margin-top: 8px; }}
.jumbo-grid > div small {{ display: block; font-size: 12px; color: #666; margin-top: 4px; font-weight: 500; }}

.stTabs [data-baseweb="tab-list"] {{ gap: 8px; background: transparent; }}
.stTabs [data-baseweb="tab"] {{
    background: {WHITE};
    border: 2px solid {PINK_BORDER};
    border-radius: 999px;
    padding: 10px 20px;
    font-weight: 700;
    color: {NAVY};
}}
.stTabs [aria-selected="true"] {{
    background: {DEEP_PINK} !important;
    border-color: {DEEP_PINK} !important;
    color: {WHITE} !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none; }}
.stTabs [data-baseweb="tab-border"] {{ display: none; }}

.contact-card {{
    background: {WHITE};
    border: 2px solid {PINK_BORDER};
    border-radius: 20px;
    padding: 10px 20px;
    box-shadow: 0 10px 24px rgba(11,31,58,0.10);
}}
.contact-title {{ font-size: 16px; font-weight: 800; color: {NAVY}; margin-bottom: 2px; }}
.contact-subtitle {{ font-size: 12px; color: #666; margin-bottom: 8px; }}
.contact-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    background: {PINK_SOFT};
    border-radius: 12px;
    padding: 8px 14px;
    margin-bottom: 6px;
}}
.contact-icon {{ font-size: 22px; width: 40px; text-align: center; }}
.contact-row small {{ display: block; color: {PINK_DARK}; font-size: 11px; font-weight: 800; letter-spacing: 1px; }}
.contact-row strong {{ color: {NAVY}; font-size: 16px; }}
.contact-row a {{ color: {DEEP_PINK}; font-weight: 700; text-decoration: none; }}
.contact-row a:hover {{ text-decoration: underline; }}
</style>
"""


def apply_theme():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_sidebar_brand():
    if st.sidebar.button("About Us", use_container_width=True, key="nav_about_us", type="primary"):
        st.session_state.stage = "about_us"
        st.rerun()

    if st.sidebar.button("Contact Info", use_container_width=True, key="nav_contact_info", type="primary"):
        st.session_state.stage = "contact_info"
        st.rerun()

    if st.sidebar.button("Dashboard", use_container_width=True, key="nav_dashboard", type="primary"):
        st.session_state.stage = "picker"
        st.rerun()

    st.sidebar.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    cols = st.sidebar.columns([1, 6, 1])
    with cols[1]:
        st.image("static/jumbo/jumbo_sidebar.png", use_container_width=True)

    st.sidebar.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    st.sidebar.page_link(
        "pages/ask_jumbo.py",
        label="🐘  Ask Jumbo",
        use_container_width=True,
    )

    st.sidebar.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if st.sidebar.button(
        "EXIT",
        use_container_width=True,
        key="sidebar_exit",
        type="primary",
    ):
        st.session_state.want_exit_confirm = True
        st.rerun()


@st.dialog("Exit Jumbo?")
def confirm_exit_dialog():
    st.write("Do you really want to exit Jumbo?")

    col_yes, col_no = st.columns(2)

    with col_yes:
        if st.button("Yes", use_container_width=True, key="exit_confirm_yes"):
            st.session_state.want_exit_confirm = False
            st.session_state.stage = "goodbye"
            st.rerun()

    with col_no:
        if st.button("No", use_container_width=True, key="exit_confirm_no"):
            st.session_state.want_exit_confirm = False
            st.rerun()


def top_banner():
    st.markdown(
        f"""
        <div style="
            margin-left: -2rem;
            margin-right: -2rem;
            margin-top: 0;
            width: calc(100% + 4rem);
            background: linear-gradient(100deg, {PINK_DARK} 0%, {DEEP_PINK} 45%, {PINK_MID} 100%);
            padding: 26px 20px 22px 20px;
            margin-bottom: 14px;
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
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_fact_bubble(fact):
    if not st.session_state.get("show_fact_bubble", True):
        return

    with st.container(key="fact_bubble_container"):
        head_col, close_col = st.columns([5, 1])

        with head_col:
            st.markdown(
                f"""
                <div style="
                    font-family: 'Trebuchet MS', 'Segoe UI', sans-serif;
                    font-weight: 800;
                    font-size: 15px;
                    color: {FACT_HEADING_COLOR};
                    letter-spacing: 0.3px;
                    text-shadow: 0 1px 2px rgba(255,255,255,0.6);
                    padding-top: 2px;
                ">🤔 Did You Know? 💡</div>
                """,
                unsafe_allow_html=True,
            )

        with close_col:
            if st.button("✕", key="fact_bubble_close"):
                st.session_state.show_fact_bubble = False
                st.rerun()

        st.markdown(
            f"""
            <div style="
                background: {FACT_BUBBLE_BG};
                border: 2px solid {FACT_BUBBLE_BORDER};
                border-radius: 30px 30px 6px 30px;
                padding: 12px 16px;
                box-shadow: 0 6px 16px rgba(0,0,0,0.15);
                text-align: left;
                margin-top: 4px;
            ">
                <div style="
                    color: {FACT_BUBBLE_TEXT};
                    font-size: 13px;
                    line-height: 1.45;
                    font-weight: 600;
                    font-family: 'Trebuchet MS', 'Segoe UI', sans-serif;
                ">🐘 {fact}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )