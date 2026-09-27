import streamlit as st
from dotenv import load_dotenv

from ui.landing import render_landing
from ui.report import render_report
from ui.styles import load_styles


load_dotenv()


st.set_page_config(
    page_title="Change Impact Investigator",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


load_styles()


if "result" not in st.session_state:

    render_landing()

else:

    result = st.session_state.result

    render_report(
        question=result["question"],
        query=result["query"],
        report=result["report"],
        ai_answer=result["ai_answer"],
    )