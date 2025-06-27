import streamlit as st
import requests

st.set_page_config(page_title="Booking Assistant", layout="centered")
st.title("AI Booking Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_bot_prompt" not in st.session_state:
    st.session_state.last_bot_prompt = ""

if "awaiting_confirmation" not in st.session_state:
    st.session_state.awaiting_confirmation = False

# --- Show the full chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Handle button press if awaiting confirmation ---
if st.session_state.awaiting_confirmation:
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Yes, book it"):
            user_input = "yes"
            st.session_state.awaiting_confirmation = False
    with col2:
        if st.button("No, cancel"):
            user_input = "no"
            st.session_state.awaiting_confirmation = False
else:
    # Normal text input
    user_input = st.chat_input("Type your message...")

# --- Process user input ---
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post("http://localhost:8000/chat", json={"user_input": user_input})
                assistant_reply = response.json()["reply"]
            except Exception as e:
                assistant_reply = f"Error from assistant:\n\n```{e}```"

        st.markdown(assistant_reply)
        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

        # If assistant is asking for booking confirmation, activate buttons
        if "Would you like to book instead at" in assistant_reply or "Do you want to book" in assistant_reply:
            st.session_state.awaiting_confirmation = True
