import streamlit as st
from openai import NOT_GIVEN

from assistant import create_thread, query, restore_messages
from settings import openai_api_key

# Show title and description.
st.title("💬 Chatbot")

last_message_id = NOT_GIVEN
# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:
    thread = create_thread()

    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []
    else:
        restore_messages(st.session_state.messages, thread)

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    if prompt := st.chat_input("What should I find?"):
        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt, unsafe_allow_html=True)

        # Generate a response using the OpenAI API.
        with st.spinner("Wait for it..."):
            print("last_message_id", last_message_id)
            response = query(prompt, thread)

        if isinstance(response, list):
            # If the response is a list of messages, display them.
            for message in response:
                if message.role == "assistant":
                    last_message_id = message.id
                    content = "\n".join(
                        c.text.value for c in message.content if c.type == "text"
                    )
                    with st.chat_message(message.role):
                        st.markdown(content, unsafe_allow_html=True)

                    st.session_state.messages.append(
                        {"role": message.role, "content": content}
                    )
        else:
            # If the response is a RunStatus object, display the error message.
            st.error(response)
