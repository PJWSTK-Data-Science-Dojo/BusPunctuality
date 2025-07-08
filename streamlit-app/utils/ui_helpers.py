import streamlit as st
from contextlib import contextmanager

@contextmanager
def loading_spinner(message="Ładowanie..."):
    with st.spinner(message):
        yield
