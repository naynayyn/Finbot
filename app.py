import streamlit as st
import plotly.express as px
import tempfile
import os

from voice.stt import transcribe_audio
from voice.tts import speak
from brain.llm import classify_and_respond
from finance.database import (
    init_db, log_expense, get_monthly_summary,
    get_budget_status, set_budget
)

# Setup
init_db()
st.set_page_config(page_title="FinBot", page_icon="💰", layout="wide")
st.title("💰 FinBot — AI Financial Advisor")

# --- Sidebar Dashboard ---
with st.sidebar:
    st.header("📊 My Dashboard")

    summary = get_monthly_summary()
    if summary:
        fig = px.pie(
            names=list(summary.keys()),
            values=list(summary.values()),
            title="This Month's Spending"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expenses logged yet!")

    st.subheader("Budget Status")
    budget_status = get_budget_status()
    if budget_status:
        for b in budget_status:
            color = "🔴" if b["percent"] > 90 else "🟡" if b["percent"] > 70 else "🟢"
            st.write(f"{color} **{b['category']}**: ${b['spent']:.0f} / ${b['limit']:.0f} ({b['percent']}%)")
    else:
        st.info("No budgets set yet!")

# --- Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- Voice Input Button ---
st.subheader("🎤 Speak to FinBot")
if st.button("🎤 Click to Record (3 seconds)"):
    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy as np

        with st.spinner("Recording... speak now!"):
            recording = sd.rec(
                int(3 * 16000),
                samplerate=16000,
                channels=1,
                dtype="float32"
            )
            sd.wait()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, recording, 16000)
            result = transcribe_audio(f.name)
            os.unlink(f.name)

        st.session_state["voice_input"] = result["text"]
        st.success(f"You said: {result['text']}")
        st.rerun()

    except Exception as e:
        st.error(f"Microphone error: {e}")

# --- Text or Voice Input ---
user_input = (
    st.chat_input("Or type your message here...")
    or st.session_state.pop("voice_input", None)
)

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Get AI response
    with st.spinner("FinBot is thinking..."):
        context = str(get_monthly_summary())
        llm_result = classify_and_respond(user_input, context)

    # Execute intent
    intent = llm_result.get("intent")
    data = llm_result.get("data", {})

    if intent == "log_expense" and data.get("amount"):
        log_expense(
            data["amount"],
            data.get("category", "Other"),
            data.get("description", "")
        )
    elif intent == "set_budget" and data.get("amount"):
        set_budget(
            data.get("category", "Other"),
            data["amount"]
        )

    # Show bot reply
    bot_reply = llm_result.get("response", "Sorry, I didn't understand that.")
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.write(bot_reply)

    # Speak the reply
    try:
        speak(bot_reply)
        st.audio("response.mp3", autoplay=True)
    except Exception:
        pass

    st.rerun()
