import logging
import os
import streamlit as st
#from model_serving_utils import query_endpoint
#from databricks import sql
import pandas as pd
#from openai import OpenAI
from dotenv import load_dotenv
import os
from mistralai import Mistral

load_dotenv() 
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_info():
    headers = st.context.headers
    return dict(
        user_name=headers.get("X-Forwarded-Preferred-Username"),
        user_email=headers.get("X-Forwarded-Email"),
        user_id=headers.get("X-Forwarded-User"),
    )

user_info = get_user_info()

st.set_page_config(
    page_title = "chatSenegal2050",
    page_icon = "💬",
    initial_sidebar_state = "expanded"
)

# Streamlit app
if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False

st.title("Senegal 2050 Chatbot")
st.markdown(
    "Ce Chatbot repond a des questions sur les communiques du Conseil des Ministres du Senegal. "
#   "[Databricks docs](https://docs.databricks.com/aws/en/generative-ai/agent-framework/chat-app) "
)


df_cm = pd.read_csv("./data/conseil_des_ministres.csv")
with st.sidebar:
    list_cm_dates = list(df_cm["date_conseil_ministres"].unique())
    list_cm_dates.sort(reverse=True)
    st.title('Quel conseil des Ministres vous interessse?')
    date_cm_user = None
    # Ask for the project ID
    #date_cm_user_input = st.text_input("Choisissez une date de Conseil des Ministres")
    date_cm_user_input = st.selectbox(
        label="Choix Date Conseil des Ministres", 
        options=list_cm_dates,
        index=0
    )
    st.write("")

    contenue_communique_cm = "\n".join(df_cm.loc[df_cm["date_conseil_ministres"] == date_cm_user_input, "communique_conseil_ministres"])

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] != "system" and ("## Context \n Voici le communique du conseil des ministres" not in message['content']):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Accept user input
prompt = None
# Create to columns and display 2 example buttons
col1, col2 = st.columns(2)
example_prompt1 = "Quelles sont les directives du president de la Republique?"
example_prompt2 = "Quelles sont les directives du premier ministre?"
button_example_1, button_example_2 = None, None
with col1:
    button_example_1 = st.button(example_prompt1)
with col2:
    button_example_2 = st.button(example_prompt2)

if button_example_1:
    prompt = example_prompt1
if button_example_2:
    prompt = example_prompt2

written_prompt = st.chat_input("Posez-vos questions sur les conseils des ministres ici...")

if written_prompt:
    prompt = written_prompt

system_prompt = """Tu es un assistant qui va repondre des questions a partit du rapport du Conseil des ministres du gouvernement senegalais, notamment les questions relatives aux directives presidentielles et celles du premier ministre. Le conseil des ministres se tient chaque semaine.
Reponds precisement a la question pose en francais en utilisant le rapport du conseil des ministres qui te sera fourni.
""".strip()
all_messages = "\n".join([message["content"] for message in st.session_state.messages])
if not system_prompt in all_messages:
    st.session_state.messages.append({"role": "system", "content": system_prompt})

if prompt:
    if contenue_communique_cm not in all_messages:
        st.session_state.messages.append({
            "role": "user",
            "content":f"## Context \n Voici le communique du conseil des ministres: {contenue_communique_cm}"
        })

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

        chat_completion = client.chat.complete(
            model= "ministral-8b-latest",
            messages = st.session_state.messages,
        )

        assistant_response = chat_completion.choices[0].message.content

        st.markdown(assistant_response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})


