import streamlit as st
import requests
import networkx as nx
import matplotlib.pyplot as plt
import time  # For streaming simulation, if needed

# Initialize session state for messages and mind map
if "messages" not in st.session_state:
    st.session_state.messages = []

if "mind_map" not in st.session_state:
    st.session_state.mind_map = nx.Graph()

if "chat_updated" not in st.session_state:
    st.session_state.chat_updated = False  # Track if chat window needs to be updated

# Fetch API keys from secrets
asu_api_key = st.secrets["asu_api"]["asu_api_key"]

# ASU API setup
asu_base_url = "https://api-edplus-poc.aiml.asu.edu/queryV2"
asu_headers = {
    'Authorization': f'Bearer {asu_api_key}',
    'Content-Type': 'application/json'
}

# Function to query ASU API
def query_asu_api(query, model="gpt4o_mini"):
    payload = {
        "model_provider": "openai",
        "model_name": model,
        "model_params": {
            "temperature": 0.7,
            "max_tokens": 1500,
            "system_prompt": "You are a helpful assistant."
        },
        "query": query,
        "enable_history": False,
        "semantic_caching": False
    }

    response = requests.post(asu_base_url, headers=asu_headers, json=payload)

    if response.status_code == 200:
        return response.json().get('response', "No 'response' in response JSON")
    else:
        st.error(f"Error querying ASU API: {response.status_code}")
        return None

# Function to stream response with write_stream
def stream_response(response):
    for word in response.split():
        yield word + " "  # Stream word by word
        time.sleep(0.05)  # Small delay to simulate real streaming

# Function to update the mind map
def update_mind_map(topic, related_topics=[]):
    st.session_state.mind_map.add_node(topic)
    for rel_topic in related_topics:
        st.session_state.mind_map.add_edge(topic, rel_topic)

# Function to display the mind map (Can be run in the background)
def display_mind_map():
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(st.session_state.mind_map)
    nx.draw(st.session_state.mind_map, pos, with_labels=True, node_color='lightblue', font_size=10)
    st.pyplot(plt)

# Streamlit App UI
st.set_page_config(page_title="Socratic Chatbot", page_icon="💬", layout="centered")
st.title("🤖 Socratic Chatbot")

# Display chat history using chat_message with custom avatars
for message in st.session_state.messages:
    avatar = ":material/surfing:" if message["role"] == "user" else ":material/raven:"  # Custom icons
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Input from user
user_input = st.chat_input("Learn About it...")

if user_input and not st.session_state.chat_updated:
    # Add user's message to chat and display it with a custom avatar
    st.chat_message("user", avatar=":material/surfing:").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Set chat_updated to True to prevent further updates until the next input
    st.session_state.chat_updated = True

    # Query ASU API for response
    response = query_asu_api(user_input)

    # Add assistant's response to chat history and stream it with `write_stream`
    if response:
        st.session_state.messages.append({"role": "assistant", "content": response})

        with st.chat_message("assistant", avatar=":material/raven:"):
            st.write_stream(stream_response(response))  # Use the native streaming method

        # Perform mind map update in the background
        update_mind_map(user_input, related_topics=[response])

    # Reset chat_updated to allow the next message
    st.session_state.chat_updated = False
