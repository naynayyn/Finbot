import streamlit as st
import plotly.express as px
import tempfile
import os
from datetime import datetime

from voice.stt import transcribe_audio
from voice.tts import speak
from brain.llm import classify_and_respond
from finance.database import (
    init_db, log_expense, get_monthly_summary,
    get_budget_status, set_budget
)

st.set_page_config(
    page_title="FinBot — AI Financial Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif !important; }

.stApp,
.stApp > div,
.main,
.main > div,
.block-container,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > div,
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] > div > div,
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottom"] > div > div,
[data-testid="stBottom"] > div > div > div,
.stChatFloatingInputContainer,
.stChatFloatingInputContainer > div,
.stChatFloatingInputContainer > div > div {
    background-color: #f8f7ff !important;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    border-right: 0.5px solid #e5e7eb !important;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: #ffffff !important;
    border: 0.5px solid #e5e7eb !important;
    border-radius: 12px !important;
    padding: 12px !important;
    margin-bottom: 8px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}

/* Chat input */
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] textarea {
    background: #ffffff !important;
    border: 0.5px solid #e5e7eb !important;
    border-radius: 12px !important;
    color: #111827 !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
    width: 100% !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* Metric cards */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 0.5px solid #e5e7eb !important;
    border-radius: 12px !important;
    padding: 16px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
[data-testid="stMetricLabel"] {
    color: #6b7280 !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
[data-testid="stMetricValue"] {
    color: #111827 !important;
    font-size: 24px !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] { font-size: 11px !important; }

/* Alert boxes */
[data-testid="stAlert"] {
    background: #f5f3ff !important;
    border: 0.5px solid #ede9fe !important;
    border-radius: 10px !important;
    color: #6b7280 !important;
}

/* Spinner */
[data-testid="stSpinner"] { color: #7c3aed !important; }
</style>
""", unsafe_allow_html=True)

USER_NAME = "Nay"
USER_INITIAL = USER_NAME[0].upper()

# ── Header ─────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between;
     background:#ffffff; border:0.5px solid #e5e7eb; border-radius:14px;
     padding:14px 24px; margin-bottom:16px;
     box-shadow:0 1px 3px rgba(0,0,0,0.06);">
  <div style="display:flex; align-items:center; gap:12px;">
    <div style="width:40px; height:40px; border-radius:10px;
         background:linear-gradient(135deg,#7c3aed,#a855f7);
         display:flex; align-items:center; justify-content:center;
         font-size:20px;">💰</div>
    <div>
      <p style="margin:0; font-size:17px; font-weight:600;
         color:#111827; letter-spacing:-0.3px;">FinBot</p>
      <p style="margin:0; font-size:11px; color:#6b7280;">
         AI Financial Advisor</p>
    </div>
  </div>
  <div style="display:flex; align-items:center; gap:12px;">
    <div style="text-align:right;">
      <p style="margin:0; font-size:13px; font-weight:500; color:#111827;">
        Hey, {USER_NAME} 👋</p>
      <p style="margin:0; font-size:11px; color:#6b7280;">
        {datetime.now().strftime("%B %Y")}</p>
    </div>
    <div style="width:40px; height:40px; border-radius:50%;
         background:linear-gradient(135deg,#7c3aed,#a855f7);
         display:flex; align-items:center; justify-content:center;
         font-size:15px; font-weight:600; color:white;">{USER_INITIAL}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Stats ──────────────────────────────────────────────────
summary = get_monthly_summary()
total_spent = sum(summary.values()) if summary else 0
budget_status = get_budget_status()
total_budget = sum(b["limit"] for b in budget_status) if budget_status else 0
budget_left = total_budget - total_spent if total_budget > 0 else 0
top_category = max(summary, key=summary.get) if summary else "None"

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("💸 Total Spent", f"${total_spent:,.0f}", delta="This month")
with col2:
    st.metric("🏦 Budget Left", f"${budget_left:,.0f}",
              delta="On track" if budget_left > 0 else "Over budget!",
              delta_color="normal" if budget_left > 0 else "inverse")
with col3:
    st.metric("🏆 Top Category", top_category)

st.markdown("<div style='margin-bottom:16px'></div>", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding:20px 0 12px;">
      <div style="width:54px; height:54px; border-radius:50%;
           background:linear-gradient(135deg,#7c3aed,#a855f7);
           display:flex; align-items:center; justify-content:center;
           font-size:20px; font-weight:600; color:white; margin:0 auto 10px;">
        {USER_INITIAL}</div>
      <p style="margin:0; font-size:15px; font-weight:600; color:#111827;">
        {USER_NAME}</p>
      <p style="margin:0; font-size:11px; color:#6b7280;">Personal Finance</p>
    </div>
    <hr style="border:none; border-top:0.5px solid #e5e7eb; margin:8px 0 16px;">
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size:12px; font-weight:600; color:#111827; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px;">📊 Spending Chart</p>', unsafe_allow_html=True)
    if summary:
        fig = px.pie(
            names=list(summary.keys()),
            values=list(summary.values()),
            hole=0.6,
            color_discrete_sequence=[
                "#7c3aed","#a855f7","#6d28d9","#c084fc","#ddd6fe"
            ]
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#111827",
            showlegend=True,
            legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
            margin=dict(t=10, b=10, l=10, r=10),
            height=200
        )
        fig.update_traces(textinfo="percent", textfont_size=10)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expenses yet! Start chatting.")

    st.markdown('<p style="font-size:12px; font-weight:600; color:#111827; text-transform:uppercase; letter-spacing:0.5px; margin:16px 0 10px;">🎯 Budget Status</p>', unsafe_allow_html=True)
    if budget_status:
        for b in budget_status:
            emoji = "🔴" if b["percent"] > 90 else "🟡" if b["percent"] > 70 else "🟢"
            bar_color = (
                "#dc2626" if b["percent"] > 90 else
                "#d97706" if b["percent"] > 70 else
                "#16a34a"
            )
            st.markdown(f"""
            <div style="margin-bottom:14px;">
              <div style="display:flex; justify-content:space-between;
                   font-size:12px; margin-bottom:5px;">
                <span style="color:#374151;">{emoji} {b['category']}</span>
                <span style="color:#7c3aed; font-weight:500;">
                  ${b['spent']:.0f} / ${b['limit']:.0f}</span>
              </div>
              <div style="height:4px; background:#f3f4f6; border-radius:2px;">
                <div style="height:4px; width:{min(b['percent'],100)}%;
                     background:linear-gradient(90deg,#7c3aed,{bar_color});
                     border-radius:2px;"></div>
              </div>
              <p style="margin:3px 0 0; font-size:10px; color:#9ca3af;
                 text-align:right;">{b['percent']}% used</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No budgets set yet!")

    st.markdown('<p style="font-size:12px; font-weight:600; color:#111827; text-transform:uppercase; letter-spacing:0.5px; margin:16px 0 10px;">⚡ Quick Actions</p>', unsafe_allow_html=True)
    if st.button("💸 Log an expense"):
        st.session_state["quick_input"] = "I want to log an expense"
    if st.button("📊 Show my summary"):
        st.session_state["quick_input"] = "Show me my spending summary"
    if st.button("💡 Give me advice"):
        st.session_state["quick_input"] = "Give me financial advice based on my spending"

# ── Chat ───────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content":
         f"Hey {USER_NAME}! 👋 I'm FinBot, your personal AI financial advisor. "
         f"Tell me about your spending, set budgets, or ask me anything "
         f"about your finances! 💰"}
    ]

for msg in st.session_state.messages:
    avatar = "💰" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

# ── Voice ──────────────────────────────────────────────────
col_voice, col_space = st.columns([1, 5])
with col_voice:
    if st.button("🎤 Record (3s)"):
        try:
            import sounddevice as sd
            import soundfile as sf
            with st.spinner("🎤 Recording... speak now!"):
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
            st.success(f"🎤 You said: *{result['text']}*")
            st.rerun()
        except Exception as e:
            st.error(f"Microphone error: {e}")

# ── Input ──────────────────────────────────────────────────
user_input = (
    st.chat_input("Message FinBot...")
    or st.session_state.pop("voice_input", None)
    or st.session_state.pop("quick_input", None)
)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    with st.spinner("✨ Thinking..."):
        context = str(get_monthly_summary())
        llm_result = classify_and_respond(user_input, context)
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
    bot_reply = llm_result.get("response", "Sorry, I didn't understand. Try again!")
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.write(bot_reply)
    try:
        speak(bot_reply)
        st.audio("response.mp3", autoplay=True)
    except Exception:
        pass
    st.rerun()
