import sys
import os
import requests
import streamlit as st

# Configure page
st.set_page_config(
    page_title="Evermemos Chat",
    page_icon="🧠",
    layout="centered"
)

st.markdown("""
<style>
/* Add any custom CSS here for the premium look */
</style>
""", unsafe_allow_html=True)

API_URL = "http://localhost:8000/chat"

def reset_chat():
    """Reset the chat history."""
    st.session_state.messages = []

def main():
    st.title("🧠 Evermemos Chat Assistant")

    with st.sidebar:
        st.header("System Controls")
        st.write("Connected to internal Evermemos Backend API.")
        
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

        with st.chat_message("assistant"):
            with st.spinner("Searching memories and synthesizing answer..."):
                try:
                    # Make HTTP request to local backend
                    res = requests.post(API_URL, json={"query": prompt, "user_id": "default"})
                    if res.status_code == 200:
                        data = res.json()
                        answer_text = data.get("answer", "No answer provided.")
                        
                        st.markdown(answer_text)
                        
                        # Optionally show some stats in expander
                        with st.expander("Retrieval Stats"):
                            st.write(f"Entities: {', '.join(data.get('entities', []))}")
                            st.write(f"Episodes: {data.get('episodes_count', 0)}")
                            st.write(f"Iterations: {data.get('iterations', 0)}")
                            st.write(f"Routed (Fast): {data.get('confidence_routed', False)}")
                            st.write(f"Reranked: {data.get('reranked', False)}")
                            
                        st.session_state.messages.append({"role": "assistant", "content": answer_text})
                    else:
                        error_msg = f"Backend error: {res.status_code} - {res.text}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                except requests.exceptions.ConnectionError:
                    error_msg = "Could not connect to the Backend API. Make sure `python main.py --api` is running on your laptop."
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()