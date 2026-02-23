import sys
import os

# Add project root to path so we can import src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Workaround for Streamlit PyTorch bug on Windows
import torch
import streamlit as st

import sys

# Add project root to path so we can import src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.evermemos import create_evermemos

# Configure page
st.set_page_config(
    page_title="Evermemos Chat",
    page_icon="🧠",
    layout="centered"
)

# Custom CSS for a cleaner, modern look
st.markdown("""
<style>
    /* Main container styling */
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Header styling */
    h1 {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #1E293B;
        font-weight: 700;
        margin-bottom: 2rem;
    }
    
    /* Chat message styling */
    .stChatMessage {
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    
    /* Assistant message specifically */
    .stChatMessage[data-testid="chat-message-assistant"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
    }
    
    /* User message specifically */
    .stChatMessage[data-testid="chat-message-user"] {
        background-color: #F0FDF4;
        border: 1px solid #DCFCE7;
    }
    
    /* Input area */
    .stChatInputContainer {
        padding-bottom: 2rem;
        border-top: 1px solid #E2E8F0;
        padding-top: 1rem;
    }
</style>
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
    
    # Sidebar for controls and stats
    with st.sidebar:
        st.header("System Controls")
        
        # Initialize system
        system = get_system()
        stats = system.get_stats()
        
        # Display stats
        st.subheader("Memory Statistics")
        st.metric("MemCells", stats.get("memcells_count", 0))
        st.metric("MemScenes", stats.get("memscenes_count", 0))
        
        st.divider()
        
        if st.button("Clear Chat History", use_container_width=True):
            reset_chat()
            st.rerun()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add a greeting message
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Hello! I am connected to your Evermemos long-term memory system. You can ask me questions about past conversations, facts, or events we've discussed!"
        })

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask me anything from your memory..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Process the query using Evermemos pipeline
        with st.chat_message("assistant"):
            with st.spinner("Searching memories and synthesizing answer..."):
                try:
                    # Use the main orchestration answer method
                    answer_text = system.answer(prompt)
                    st.markdown(answer_text)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": answer_text})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error while searching memory: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()
