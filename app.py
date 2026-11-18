import streamlit as st

st.set_page_config(page_title="Corrector INAL Coca", page_icon="🧾", layout="wide")

from inal_coca.ui import render  # noqa: E402

render()
