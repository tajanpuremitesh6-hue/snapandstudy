
import os
import json
from urllib import error, request

try:
    from google import genai
    from google.genai import types
except ModuleNotFoundError:
    genai = None
    types = None

import streamlit as st

from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE, SUMMARY_REQUEST_PROMPT


try:
    secrets = st.secrets
except Exception:
    secrets = {}

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or secrets.get("GEMINI_API_KEY", "")
MODEL_NAME = "gemini-2.5-flash"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or secrets.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = str(
    os.environ.get("TELEGRAM_CHAT_ID") or secrets.get("TELEGRAM_CHAT_ID", "")
).strip()



@st.cache_resource
def get_gemini_client(api_key: str):
    if not api_key or genai is None:
        return None
    return genai.Client(api_key=api_key)


gemini_client = get_gemini_client(GEMINI_API_KEY)

if genai is None:
    st.error("Missing dependency: install it with 'pip install -r requirements.txt'.")
    st.stop()

if not GEMINI_API_KEY:
    st.warning("Set the GEMINI_API_KEY environment variable or add it to .streamlit/secrets.toml to continue.")
    st.stop()


def clean_telegram_text(text):
    if not text:
        return "No summary available."
    text = text.strip()
    return text[:1500] + "\n\n[Summary shortened]" if len(text) > 1500 else text


def send_telegram(chat_id, summary):
    if not TELEGRAM_BOT_TOKEN:
        return False, "Set TELEGRAM_BOT_TOKEN in the environment or .streamlit/secrets.toml."
    try:
        payload = json.dumps({"chat_id": chat_id, "text": clean_telegram_text(summary)}).encode("utf-8")
        telegram_request = request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(telegram_request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not result.get("ok"):
            return False, result.get("description", "Telegram could not send the message.")
        return True, str(result["result"]["message_id"])
    except error.HTTPError as exception:
        try:
            result = json.loads(exception.read().decode("utf-8"))
            return False, result.get("description", f"Telegram request failed (HTTP {exception.code}).")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False, f"Telegram request failed (HTTP {exception.code})."
    except error.URLError as exception:
        return False, str(exception.reason)
    except Exception as exception:
        return False, str(exception)






def render_message(message):
    with st.chat_message(message["role"]) :
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])




def add_message(role , kind,content):
    st.session_state.messages.append({"role": role,"kind": kind,"content": content })
    render_message(st.session_state.messages[-1])



def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text
    except Exception as error:
        return f"Sorry, Something went wrong:{error}"




# step 1: onboarding page (name and Telegram chat ID)
if "onboarding" not in st.session_state or "telegram_chat_id" not in st.session_state:
    st.session_state.onboarding = True

if st.session_state.onboarding:
    st.title("Welcome to Snap & Study! 📚")

    with st.form("onboarding_form"):
        name = st.text_input("Enter your name:", key="name_input")
        if TELEGRAM_CHAT_ID:
            telegram_chat_id = TELEGRAM_CHAT_ID
            st.caption("Telegram chat ID loaded from secrets.")
        else:
            telegram_chat_id = st.text_input(
                "Telegram chat ID",
                key="telegram_chat_id_input",
                placeholder="123456789",
                help="Start a chat with your Telegram bot first, then enter your chat ID.",
            )

        submitted = st.form_submit_button("Submit")

        if submitted and (not name.strip() or not telegram_chat_id.strip()):
            st.warning("Please enter both your name and Telegram chat ID.")
            st.stop()

    if submitted:
        if not name.strip() or not telegram_chat_id.strip():
            st.warning("Please enter both your name and Telegram chat ID.")
        else:
            st.session_state.name = name.strip()
            st.session_state.telegram_chat_id = telegram_chat_id.strip()

            system_instruction = "You are Snap & Study, an AI study assistant helping the user learn and improve their study habits."
            chat_client = getattr(gemini_client, "chats", getattr(gemini_client, "chat", None))
            if chat_client is None:
                st.error("Gemini chat client is unavailable. Please check your Google GenAI SDK version.")
                st.stop()
            #activate my ai
            st.session_state.chat = chat_client.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
            )
            st.session_state.messages = []
            st.session_state.onboarding = False
            st.rerun()

    st.stop()


telegram_chat_id = TELEGRAM_CHAT_ID or st.session_state.telegram_chat_id

# create a chat interface 

header_col, button_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("SnapandStudy 📚")


with button_col:
    send_disabled = len(st.session_state.messages) <= 1 

    if st.button("Send summary to Telegram", disabled=send_disabled, use_container_width=True):
        with st.spinner("Summarizing and sending... "):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT]) 
        success, info = send_telegram(telegram_chat_id, summary)

        if success:
            st.success("Summary sent to Telegram successfully!")
        else:
            st.error(f"Failed to send summary to Telegram: {info}")
    
st.caption(f"Logged in as {st.session_state.name} - summaries will be sent to Telegram chat {telegram_chat_id}")


if not st.session_state.messages:
    add_message("assistant", "text", WELCOME_MESSAGE.format(name=st.session_state.name))
else:
    for message in st.session_state.messages:
        render_message(message)     



user_input = st.chat_input(
    "Ask a question , or attach a image of your notes,textbook,or question paper to get started",
    accept_file = True,
    file_type = ["jpg","png","jpeg","pdf"],
)

if user_input: 
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text 
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user","image",photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))

    if text:
        add_message("user","text",text)
        parts.append(text)
    
    elif photo is not None:
        parts.append("what is this image about? give me a simple explanation and a summary of the key points to remember.)") 

    with st.spinner("Analyzing your input..."):
        answer = ask_gemini(parts) 
    add_message("assistant","text",answer)    
    st.rerun()


