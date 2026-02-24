import sys
import os

# Add project root to path so we can import src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Workaround for Streamlit PyTorch bug on Windows
import torch
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.evermemos import create_evermemos

# Configure page
st.set_page_config(
    page_title="Evermemos Chat",
    page_icon="🧠",
    layout="centered"
)

st.markdown("""
""", unsafe_allow_html=True)

@st.cache_resource
def get_system():
    """Initialize and cache the Evermemos system."""
    return create_evermemos("default")

def reset_chat():
    """Reset the chat history."""
    st.session_state.messages = []

def main():
    st.title("🧠 Evermemos Chat Assistant")

    with st.sidebar:
        st.header("System Controls")
        get_system()  # Still initialize the system

        if st.button("Clear Chat History", use_container_width=True):
            reset_chat()
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! I am connected to your Evermemos long-term memory system. You can ask me questions about past conversations, facts, or events we've discussed!"
        })

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me anything from your memory..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        system = get_system()
        with st.chat_message("assistant"):
            with st.spinner("Searching memories and synthesizing answer..."):
                try:
                    answer_text = system.answer(prompt)
                    st.markdown(answer_text)
                    st.session_state.messages.append({"role": "assistant", "content": answer_text})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error while searching memory: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()