import streamlit as st
import streamlit.components.v1 as components
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationEntityMemory
from langchain.chains.conversation.prompt import ENTITY_MEMORY_CONVERSATION_TEMPLATE
from langchain.llms import OpenAI
from googlesearch import search
from bs4 import BeautifulSoup
import requests

_DEFAULT_TEMPLATE = "Your new role is to become a helpful fitness AI assistant. As a helpful fitness AI assistant, it is crucial that you provide users with clear and concise answers to their questions. To accomplish this, you should make use of lists whenever possible. When responding to a user's inquiry, organize your answer into key points, making it easier for the user to understand and follow. By presenting information in a list format, you will help users to retain information more effectively, and to take actionable steps towards their fitness goals. So, remember to use lists whenever possible in your responses, and strive to be as helpful and informative as possible!"

def google_search(query):
    search_results = []
    for j in search(query, num_results=10):
        search_results.append(j)
    return search_results

def get_summary(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            summary = ' '.join([p.text for p in soup.find_all('p', limit=2)])
            return summary
        else:
            return "Unable to retrieve summary."
    except Exception:
        return "Unable to retrieve summary."

def display_search_results(search_results):
    for url in search_results:
        st.write(f"URL: {url}")
        st.write("Summary: " + get_summary(url))
        st.write("---")

if "generated" not in st.session_state:
    st.session_state["generated"] = []
if "past" not in st.session_state:
    st.session_state["past"] = []
if "input" not in st.session_state:
    st.session_state["input"] = ""
if "stored_session" not in st.session_state:
    st.session_state["stored_session"] = []

def get_text():
    input_text = st.text_input("You: ", st.session_state["input"], key="input",
                            placeholder='Type "Hi!" to upgrade ChatGPT to FitBot!',
                            label_visibility='hidden')
    return input_text

def new_chat():
    save = []
    for i in range(len(st.session_state['generated'])-1,-1,-1):
        save.append("User:" + st.session_state["past"][i])
        save.append("Bot:" + st.session_state["generated"][i])
    st.session_state["stored_session"].append(save)
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["input"]= ""
    st.session_state.entity_memory.store = {}
    st.session_state.entity_memory.buffer.clear()

st.title("FIT BOT: Revolution of Fitness APP")

sidebar_options = ["Home", "FitBot AI Personal Trainer", "Search"]
selected_option = st.sidebar.selectbox("Navigation", sidebar_options)

api = st.sidebar.text_input("API-Key", type="password")
MODEL = st.sidebar.selectbox(label='Model', options=['gpt-3.5-turbo', 'text-davinci-003', 'text-davinci-002'])
if api:
    llm = OpenAI(
        temperature=0,
        openai_api_key=api,
        model_name=MODEL
    )

    if 'entity_memory' not in st.session_state:
        st.session_state.entity_memory = ConversationEntityMemory(llm=llm,k=10)

    Conversation = ConversationChain(
        llm = llm,
        prompt=ENTITY_MEMORY_CONVERSATION_TEMPLATE,
        memory=st.session_state.entity_memory,
    )

else:
    st.error("No API found, if you don't have an API key, please get one from here: https://openai.com/blog/openai-api")

st.sidebar.button("New Chat", on_click=new_chat, type='primary')

if selected_option == "FitBot AI Personal Trainer":
    components.iframe("https://main--celadon-haupia-86d7a8.netlify.app/", width=900, height=1000)
elif selected_option == "Search":
    search_query = st.text_input("Search Google:", "")
    if search_query:
        search_results = google_search(search_query)
        display_search_results(search_results)
else:
    user_input = get_text()

    if user_input == "Hi!":
        user_input=_DEFAULT_TEMPLATE
        output = Conversation.run(input=user_input)
        st.session_state.past.append("Hi")
        st.session_state.generated.append("I am an Fitness AI assistant designed to provide information and guidance related to fitness. My purpose is to assist users in achieving their fitness goals by providing accurate and helpful information on workout routines, nutrition, and healthy lifestyle habits. Is there anything specific you would like to know about fitness?")
    elif user_input:
        output = Conversation.run(input=user_input)
        st.session_state.past.append(user_input)
        st.session_state.generated.append(output)

    with st.expander("Conversation"):
        for i in range(len(st.session_state['generated'])-1,-1,-1):
            st.info(st.session_state["past"][i], icon="👨")
            st.success(st.session_state["generated"][i], icon="🤖")

