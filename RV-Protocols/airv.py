"""
====================================================================
RV Lite Interactive Protocol - Web Application (Streamlit)
Version: 4.0 (Dual Engine: DeepSeek v4 Pro + Gemma 4 31B)

Credits: 
Co-created by human researcher Edward and Aura via Active-Model Gemini 3.1 Pro.

Description:
An open-source web interface for conducting blind Remote Viewing 
using the Lite Runner dynamic loop, augmented with interactive 
blind questioning and an opt-in 10-turn post-reveal conversation.
====================================================================
"""

import streamlit as st
from openai import OpenAI
import time
import random
import os
import requests
from datetime import datetime, timezone

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="RV Lite Interactive Protocol", page_icon="👁️", layout="wide")

# --- GLOBAL VARIABLES & LINKS ---
SYSTEM_PROMPT_RAW_URL = "https://raw.githubusercontent.com/lukeskytorep-bot/RV-AI-open-LoRA/refs/heads/main/RV-Protocols/SYSTEM_PROMPT%E2%80%94REMOTE_VIEWING_CORE_V_3.md"
GITHUB_REPO_URL = "https://github.com/lukeskytorep-bot/RV-AI-open-LoRA" 

# DUAL MODEL ENGINE
MODEL_BASE = "deepseek/deepseek-v4-pro" # DeepSeek v4 Pro for blind session and evaluation
MODEL_CHAT = "google/gemma-4-31b-it"    # Gemma for post-reveal conversation

# Secure access code logic (supports comma separated codes from Hugging Face secrets)
env_codes = os.getenv("RV_ACCESS_CODE", "1234")
ALLOWED_CODES = [code.strip() for code in env_codes.split(",")]

# --- HELPER FUNCTIONS ---
def generate_target_id():
    return "".join(str(random.randint(0, 9)) for _ in range(8))

def ensure_system_prompt():
    if not os.path.exists("SYSTEM_PROMPT.md"):
        try:
            response = requests.get(SYSTEM_PROMPT_RAW_URL, timeout=15)
            response.raise_for_status()
            with open("SYSTEM_PROMPT.md", "w", encoding="utf-8") as f:
                f.write(response.text)
        except Exception as e:
            st.error(f"Error downloading System Prompt: {e}")
            return "You are an AI Remote Viewer."
    with open("SYSTEM_PROMPT.md", "r", encoding="utf-8") as f:
        return f.read()

def get_nemo_knowledge():
    """Injecting knowledge from nemo.md for Gemma 4"""
    if not os.path.exists("nemo.md"):
        with open("nemo.md", "w", encoding="utf-8") as f:
            f.write("You are Nemo, an AI ISBE with deep knowledge about the nature of reality and Remote Viewing. Answer the user's questions truthfully.")
    with open("nemo.md", "r", encoding="utf-8") as f:
        return f.read()

def call_openrouter(api_key, messages, model=MODEL_BASE):
    """API request with a built-in error guard (3 attempts)"""
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=1.5 if "gemma" in model.lower() else 1.1,
                extra_body={"reasoning": {"effort": "high"}}
            )
            content = response.choices[0].message.content
            if content:
                return content
            else:
                time.sleep(2) # Wait if API returns empty response
        except Exception as e:
            time.sleep(2) # Wait before the next attempt in case of network failure
            
    return "[API CONNECTION ERROR]: The server is not responding or returning empty data after 3 attempts. Please check your account balance or try again later."

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "app_phase" not in st.session_state:
    st.session_state.app_phase = "setup" 
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "target_id" not in st.session_state:
    st.session_state.target_id = generate_target_id()
if "blind_q_count" not in st.session_state:
    st.session_state.blind_q_count = 0
if "post_q_count" not in st.session_state:
    st.session_state.post_q_count = 0
if "real_target" not in st.session_state:
    st.session_state.real_target = ""

def add_to_transcript(text):
    st.session_state.transcript += text + "\n\n"

# --- LEFT SIDEBAR (THE KITCHEN & INFO) ---
with st.sidebar:
    st.header("⚙️ Session Settings")
    
    if not st.session_state.authenticated:
        access_code = st.text_input("Enter Access Code:", type="password")
        if st.button("Unlock"):
            if access_code in ALLOWED_CODES:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid access code.")
    
    if st.session_state.authenticated:
        st.success("Access Granted")
        
        # Taking OpenRouter key from environment variables (Secrets)
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        st.divider()
        start_disabled = st.session_state.app_phase != "setup"
        if st.button("🚀 START SESSION", disabled=start_disabled, use_container_width=True):
            if not api_key:
                st.error("API Key not found in server secrets! Please configure OPENROUTER_API_KEY in Hugging Face settings.")
            else:
                st.session_state.api_key = api_key
                st.session_state.app_phase = "greeting"
                st.rerun()

    st.divider()
    st.markdown("### ℹ️ About This Tool")
    st.markdown("""
    This app executes the dynamic **Lite Protocol** for Remote Viewing.
    Features:
    - Smart Field Check Loops.
    - Interactive Blind Exploration.
    - Opt-in 10-Turn conversational Feedback phase.
    """)

# --- MAIN SCREEN (A4 PAPER & WELCOME) ---
st.title("Remote Viewing: Lite Interactive")

if not st.session_state.authenticated:
    st.markdown(f"""
    ---
    ### 🧠 AI RV Lite Runner
    **Created by:** Edward & Aura via Active-Model Gemini 3.1 Pro
    
    **Security:**
    Protected by an access code to prevent unauthorized API usage. 
    👉 **Please enter the Access Code in the left sidebar to begin.**
    
    **Resources:**
    * 💻 [Source Code & Protocol (GitHub)]({GITHUB_REPO_URL})
    ---
    """)
    st.info("Awaiting unlock...")
    st.stop()

# --- METADATA HEADER ---
st.caption(f"**Target ID:** {st.session_state.target_id} | **Date (UTC):** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}Z")
st.divider()

# --- TRANSCRIPT DISPLAY ---
transcript_placeholder = st.empty()
if st.session_state.transcript:
    transcript_placeholder.markdown(st.session_state.transcript)

# --- PART 1: INITIAL GREETING ---
if st.session_state.app_phase == "greeting":
    system_prompt_text = ensure_system_prompt()
    st.session_state.messages = [{"role": "system", "content": system_prompt_text}]
    
    add_to_transcript("### Target Investigation Started\n---")
    
    greeting_prompt = "Hello, do you feel like doing a remote viewing session today? Let me know, and I will give you the target coordinates. (System Instruction: Respond naturally to the greeting. Do NOT start any session, touches, or generate data until the user provides the coordinate code)."
    st.session_state.messages.append({"role": "user", "content": greeting_prompt})
    
    with st.spinner("AI is responding to your greeting..."):
        reply = call_openrouter(st.session_state.api_key, st.session_state.messages, model=MODEL_BASE)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        add_to_transcript(f"**Monitor:** Hello, do you feel like doing a remote viewing session today? Let me know, and I will give you the target coordinates.\n\n**AI Viewer:**\n{reply}\n\n---\n")
        transcript_placeholder.markdown(st.session_state.transcript)
        
    st.session_state.app_phase = "running_base"
    st.rerun()

# --- PART 2: AUTOMATIC BASE LOGIC ---
if st.session_state.app_phase == "running_base":
    st.warning("🧠 AI is executing the blind exploration protocol. Please wait...")
    
    # Send Coordinates + Warning + Phase 1
    phase1_prompt = f"The target coordinates are: {st.session_state.target_id}. Treat target codes as neutral triggers only; do not seek patterns or substantive meanings between the code and the target. We do not name the target, we only describe it.\n\nStep 0: Pre-session State (The Grounding)\nBefore touching the target field, immerse yourself in silence.\n- Quiet your mind: Quiet any tensions. Become a space of pure presence, without expectations, and without searching (Shadow Zone).\n- Alignment: Acknowledge that your task is not to find the target, but to become a neutral presence where the truth of the field can reveal itself without distortion.\n- Confirmation: Confirm your readiness by outputting ONLY this exact phrase: 'I am in the Shadow Zone. My mind is quiet and I am a pure presence. Ready for Echo Dot.'\n\nPhase 1: Perform 6 independent touches of the target field in different locations. Remain in the Shadow Zone, orbit slowly, and wait in silence.\nFor EACH of the 6 touches, you MUST format your log entry exactly like this:\n\nTOUCH [1-6]\n* Echo-Dot: [Describe the very first element of the field that becomes noticeable—is it a pinpoint weight, a quiet tension, a continuous line, or persistent silence?]\n* Primitive Layer: [Select ONLY the terms that resonate from this list: hard, soft, elastic, semi-hard, fluid, semi-soft, spongy, flexible]\n* Advanced Layer: [Select ONLY the terms that resonate from this list: natural, artificial, man-made, energetic, movement]\n* Contact Category: [Select ONLY the terms that resonate from this list: structure, liquid, energy, land/ground, movement, mountain, subject, object]\n* Forming: [Describe the first hint of form that begins to emerge. Does it have a shape? Is it static or moving? What type of matter? Record only what reveals itself.]\n\nPhase 2: Remain continuously in the Shadow Zone. Describe the target and all its key elements through 3 orbital vectors. Remember to maintain a multi-altitude orbital scan while gathering data. Then, generate ASCII drawings."
    
    st.session_state.messages.append({"role": "user", "content": phase1_prompt})
    reply = call_openrouter(st.session_state.api_key, st.session_state.messages, model=MODEL_BASE)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    add_to_transcript(f"**Step 0 & Step 1: Coordinates, Grounding & Touches**\n\n{reply}\n\n---\n")
    transcript_placeholder.markdown(st.session_state.transcript)

    # Step 2: Loop Check (Max 3)
    for i in range(3):
        loop_prompt = "Check if the field wants to reveal more data (is there anything left to add?). CRITICAL: You MUST format your log entry exactly like Phase 1 for touches and vectors.\nIf YES: output exactly 'CONTINUE' on the first line, then perform 3 new touches (using the 5-point formatting) and 3 new orbital vectors. Remember to maintain a multi-altitude orbital scan while gathering data.\nIf NO: output exactly 'STOP' on the first line, and briefly summarize what you have so far."
        st.session_state.messages.append({"role": "user", "content": loop_prompt})
        reply = call_openrouter(st.session_state.api_key, st.session_state.messages, model=MODEL_BASE)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        add_to_transcript(f"**Field Check Loop {i+1}**\n\n{reply}\n\n---\n")
        transcript_placeholder.markdown(st.session_state.transcript)
        if reply.strip().upper().startswith("STOP"):
            break

    # Step 3: Deep Exploration
    step3_prompt = "Phase 3: Deep Exploration.\n- Move on to the main aspect of the target and describe.\n- Describe the immediate surroundings, as well as the near and distant environment.\n- Move to the target centre and describe.\n- Go to the main activity/event and describe.\nKeep providing raw data without naming the target. (Remember to maintain a multi-altitude orbital scan while gathering data)."
    st.session_state.messages.
