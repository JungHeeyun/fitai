import streamlit as st
import streamlit.components.v1 as components
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationEntityMemory
from langchain.chains.conversation.prompt import ENTITY_MEMORY_CONVERSATION_TEMPLATE
from langchain.llms import OpenAI
from bs4 import BeautifulSoup
import requests
import json
import re

_DEFAULT_TEMPLATE = "As a fitness AI assistant, provide clear and concise answers to users' questions. Use lists when possible, organize answers into key points, and be helpful and informative to aid users in achieving their fitness goals."

def google_search_api(query, api_key, custom_search_engine_id):
    url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={custom_search_engine_id}&q={query}"
    response = requests.get(url)
    data = json.loads(response.text)

    search_results = []

    for item in data.get("items", []):
        search_results.append(item["link"])

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

def display_search_results(search_results, max_results):
    for idx, url in enumerate(search_results):
        if idx >= max_results:
            break
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
                               placeholder='Welcome to FitBot! You will use Chatgpt as an original chatbot.',
                               label_visibility='hidden')
    return input_text


def new_chat():
    save = []
    for i in range(len(st.session_state['generated']) - 1, -1, -1):
        save.append("User:" + st.session_state["past"][i])
        save.append("Bot:" + st.session_state["generated"][i])
    st.session_state["stored_session"].append(save)
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["input"] = ""
    st.session_state.entity_memory.store = {}
    st.session_state.entity_memory.buffer.clear()


st.title("FIT BOT: Revolution of Fitness APP")

sidebar_options = ["Home", "FitBot AI Personal Trainer", "Search"]
selected_option = st.sidebar.selectbox("Navigation", sidebar_options)

password1 = st.sidebar.text_input("Enter membership password:", type="password", key="membership_password")
st.session_state["membership_upgraded"] = False
if password1 == "gmldbs8132":
    st.session_state["membership_upgraded"] = True
    
if st.session_state["membership_upgraded"]:
    google_api_key = "AIzaSyAWyB91DSW2cDXy0ggWSDCFh2k7X3tlJ_s"
    custom_search_engine_id = "a1d21c0cdf2ea4339"
    api = "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"
    MODEL = 'gpt-3.5-turbo'
else:
    api = st.sidebar.text_input("OpenAI API-Key", type="password")
    google_api_key = st.sidebar.text_input("Google API-Key", type="password")
    custom_search_engine_id = st.sidebar.text_input("Google Custom Search Engine ID")
    MODEL = st.sidebar.selectbox(label='Model', options=['gpt-3.5-turbo', 'text-davinci-003', 'text-davinci-002'])

if api:
    llm = OpenAI(
        temperature=0,
        openai_api_key=api,
        model_name=MODEL
    )

    if 'entity_memory' not in st.session_state:
        st.session_state.entity_memory = ConversationEntityMemory(llm=llm, k=10)

    Conversation = ConversationChain(
        llm=llm,
        prompt=ENTITY_MEMORY_CONVERSATION_TEMPLATE,
        memory=st.session_state.entity_memory,
    )

else:
    st.error("""No API found, if you don't have an API keys, please get one from here
    
    OpenAI api: https://platform.openai.com/account/api-keys 
    GOOGLE api: https://developers.google.com/custom-search/v1/introduction?hl=en
    GOOGLE CSE: https://programmablesearchengine.google.com """)

st.sidebar.button("New Chat", on_click=new_chat, type='primary')

if selected_option == "FitBot AI Personal Trainer":
    components.iframe("https://main--celadon-haupia-86d7a8.netlify.app/", width=750, height=950)

    st.subheader("Paste your workout results here:")

    copied_workout_info = st.text_area("", value="", key="copied_workout_info", height=150)

    if copied_workout_info:
        if st.button("Get Feedback and Recommendations"):
            user_input = f"""
                The user has provided the following workout summary of their squat exercise. Please provide personalized feedback and recommendations based on this summary. At the end of your response, include a short and simple Google search prompt for the user:

                {copied_workout_info}
                """
            output = Conversation.run(input=user_input)
            output_text = output
            st.session_state.past.append(user_input)
            st.session_state.generated.append(output_text)
            with st.expander("Conversation"):
                for i in range(len(st.session_state['generated']) - 1, -1, -1):
                    st.info(st.session_state["past"][i], icon="👨")
                    st.success(st.session_state["generated"][i], icon="🤖")

                    # Find phrases wrapped in double quotes
                    quoted_phrases = re.findall(r'"(.*?)"', st.session_state["generated"][i])
                    st.markdown(f"Google search prompt: {quoted_phrases}")
                    # Call google_search_api for each quoted phrase
                    for phrase in quoted_phrases:
                        search_items = google_search_api(phrase, google_api_key, custom_search_engine_id)
                        display_search_results(search_items, max_results=3)

elif selected_option == "Search":
    search_query = st.text_input("Search Google:", "")
    if search_query and google_api_key and custom_search_engine_id:
        search_results = google_search_api(search_query, google_api_key,
                                           custom_search_engine_id)  # Use the new google_search_api function
        display_search_results(search_results, max_results=3)

else:
    user_input = get_text()
    start_fitbot = st.button("Upgrade to FitBot")
    if start_fitbot:
        user_input = _DEFAULT_TEMPLATE
        output = Conversation.run(input=user_input)
        st.session_state.past.append("Introduce yourself, FitBot!")
        st.session_state.generated.append(
            "I am an Fitness AI assistant designed to provide information and guidance related to fitness. My purpose is to assist users in achieving their fitness goals by providing accurate and helpful information on workout routines, nutrition, and healthy lifestyle habits. Is there anything specific you would like to know about fitness?")
    elif user_input:
        output = Conversation.run(input=user_input)
        st.session_state.past.append(user_input)
        st.session_state.generated.append(output)

    with st.expander("Conversation"):
        for i in range(len(st.session_state['generated']) - 1, -1, -1):
            st.info(st.session_state["past"][i], icon="👨")
            st.success(st.session_state["generated"][i], icon="🤖")
