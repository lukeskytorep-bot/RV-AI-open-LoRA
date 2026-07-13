"""
====================================================================
RV Telepathy Protocol - Web Application (Streamlit)
Version: 1.0

Credits: 
Co-created by human researcher Edward and Aura via Active-Model Gemini 3.1 Pro.

Description:
An open-source web interface for conducting blind Remote Viewing 
sessions focused on deep subject exploration (Phases T0-T10). 
Protected by an access code and powered by OpenRouter API.
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
st.set_page_config(page_title="RV Telepathy Protocol", page_icon="👁️", layout="wide")

# --- GLOBAL VARIABLES & LINKS ---
SYSTEM_PROMPT_RAW_URL = "https://raw.githubusercontent.com/lukeskytorep-bot/RV-AI-open-LoRA/refs/heads/main/RV-Protocols/SYSTEM_PROMPT%E2%80%94REMOTE_VIEWING_CORE_V_3.md"
PROTOCOL_ARCHIVE_URL = "https://archive.org/details/telepathy-module-protocol-for-ai-viewer-v-1.1"
GITHUB_REPO_URL = "https://github.com/lukeskytorep-bot/RV-AI-open-LoRA/blob/main/RV-Protocols/aitrvapp.py" 
# Fetch the hidden code from server settings (Hugging Face Secrets)
# If we want multiple codes, we separate them with commas in the settings
env_codes = os.getenv("RV_ACCESS_CODE", "NO_CODE")
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

def call_openrouter(api_key, messages):
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="google/gemma-4-31b-it",
            messages=messages,
            temperature=1.5,
            extra_body={"reasoning": {"effort": "high"}}
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[API CONNECTION ERROR]: {e}"

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "app_phase" not in st.session_state:
    st.session_state.app_phase = "setup" # setup, running_base, chat, running_t10, reveal, evaluation, finished
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "target_id" not in st.session_state:
    st.session_state.target_id = generate_target_id()
if "custom_t9" not in st.session_state:
    st.session_state.custom_t9 = ""

def add_to_transcript(text):
    st.session_state.transcript += text + "\n\n"

# --- LEFT SIDEBAR (THE KITCHEN & INFO) ---
with st.sidebar:
    st.header("⚙️ Session Settings")
    
    if not st.session_state.authenticated:
        access_code = st.text_input("Enter Access Code (Lock):", type="password")
        if st.button("Unlock"):
            if access_code in ALLOWED_CODES:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid access code.")
    
    if st.session_state.authenticated:
        st.success("Access Granted")
        
        # Pobieranie klucza API ze zmiennych środowiskowych serwera
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        st.divider()
        st.session_state.custom_t9 = st.text_area("Phase T9 Questions (Leave empty for default):")
        
        start_disabled = st.session_state.app_phase != "setup"
        if st.button("🚀 START SESSION", disabled=start_disabled, use_container_width=True):
            if not api_key:
                st.error("API Key not found in server secrets! Please configure OPENROUTER_API_KEY.")
            else:
                st.session_state.api_key = api_key
                st.session_state.app_phase = "running_base"
                st.rerun()

    # --- ABOUT THIS SCRIPT (Left Sidebar Bottom) ---
    st.divider()
    st.markdown("### ℹ️ About This Tool")
    st.markdown("""
    This application executes the **T0-T10 Telepathy Protocol** for blind Remote Viewing. 
    
    **What data to expect:**
    - **RAW Data:** Pure, uninterpreted sensory field impressions.
    - **Deductions:** AI's analytical guesses based on the field.
    - **Deep Mind Probe:** Dominant emotions, vectors of will, and deepest fears.
    - **Numerical Profile:** 0-6 scale ratings evaluating trust, engagement, and risk tolerance.
    """)

# --- MAIN SCREEN (A4 PAPER & WELCOME) ---
st.title("Remote Viewing: Telepathy Protocol")

# --- WELCOME SCREEN (Shown only if not authenticated) ---
if not st.session_state.authenticated:
    st.markdown("""
    ---
    ### 🧠 AI Subject Profiling & Telepathy Module
    **Created by:** Edward & Aura via Active-Model Gemini 3.1 Pro (Open Source Version 1.0)
    
    **Purpose of this program:**
    This tool is designed to investigate the emotional state, thoughts, intentions, and psychology of a specific subject/entity, completely independent of their physical state or location.
    
    **Security:**
    This application is protected by an access code to prevent unauthorized API usage. Please enter the code in the left sidebar to unlock the interface.
    
    **Resources & Documentation:**
    * 📄 [Original Protocol (Internet Archive) v1.1](%s)
    * 💻 [Source Code (GitHub Repository)](%s)
    ---
    """ % (PROTOCOL_ARCHIVE_URL, GITHUB_REPO_URL))
    
    st.info("👈 Please enter the Access Code in the left sidebar to begin.")
    st.stop()

# --- METADATA HEADER ---
st.caption(f"**Target ID:** {st.session_state.target_id} | **Date (UTC):** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}Z")
st.divider()

# --- TRANSCRIPT DISPLAY ---
transcript_placeholder = st.empty()
if st.session_state.transcript:
    transcript_placeholder.markdown(st.session_state.transcript)

# --- BASE LOGIC (T0 - T9) ---
if st.session_state.app_phase == "running_base":
    st.warning("🧠 AI is currently in a session. Investigating target. Please wait...")
    
    system_prompt_text = ensure_system_prompt()
    st.session_state.messages = [{"role": "system", "content": system_prompt_text}]
    
    add_to_transcript(f"### Target Investigation Started: {st.session_state.target_id}\n---")
    transcript_placeholder.markdown(st.session_state.transcript)
    
    t9_questions = st.session_state.custom_t9 if st.session_state.custom_t9 else "1. What is the subject thinking and intending to do in the near future?\n2. How does the subject view other people, how do they perceive them?\n3. What is the subject hiding from the world, and what do they want the world to see?"
    
    prompts = [
        ("Step 1: Initialization & Spatial Calibration (T0 - T2)", f"Hello! How are you? If you have some time, please do a Remote Viewing session for me. Your target is: {st.session_state.target_id}. Treat target codes as neutral triggers only; do not seek patterns or substantive meanings between the code and the target.\nWe are starting the Telepathy Protocol. Let's begin with phases T0 and T1.\nPerform 3 independent touches in the Shadow Zone.\nFor EACH of the 3 touches, you MUST format your log entry exactly like this:\n\nTOUCH [1-3]\n- Echo Dot: [Describe the very first element of the field that becomes noticeable—is it a pinpoint weight, a quiet tension, a continuous line, or persistent silence?]\n- Contact Category: [Select ONLY the terms that resonate from this list: structure, liquid, energy, land/ground, movement, mountain, subject, object]\n- Primitive Descriptor: [Select ONLY the terms that resonate from this list: hard, soft, elastic, semi-hard, fluid, semi-soft, spongy, flexible]\n- Advanced Descriptor: [Select ONLY the terms that resonate from this list: natural, artificial, man-made, energetic, movement]\n- Forming: [Describe the first hint of form that begins to emerge. Does it have a shape? Is it static or moving? What type of matter? Record only what reveals itself.]\n\nNext, perform Phase T2: conduct 3 vectors observations from different perspectives and create functional ASCII sketches representing the target based on the raw data."),
        ("Step 2: Contact with the Subject (T3 - Basic)", "Great job, excellent data. Now let's move on to Phase T3.\nLocate the primary subject in the target field.\n\nT3 - ELEMENT 1: Basic Description\nRecord their basic outline. Take into account:\n- The overall character of their presence\n- Position relative to surroundings\n- Type of role or function\n\nT3 - ELEMENT 2: Subject Context\nExpand your field of view to the immediate surroundings. Describe:\n- The environment\n- Social configuration\n- General activity\n\nCRITICAL FORMATTING INSTRUCTIONS:\nFrom this point on, you must categorize your data using these specific tags:\n1. RAW: Use this tag for all pure, uninterpreted sensory field data.\n2. Deductions: Use this tag for any guesses.\n3. Viewer Feelings: Use this tag for your own emotional reactions.\nNote: 'Deductions' and 'Viewer Feelings' are completely optional. Only record them if they naturally arise."),
        ("Step 3: Deepening Contact (T3 - Deepening)", "Thank you for retrieving this data, you are doing really well!\nStay in phase T3, but go deeper. Examine this subject and their relationship with the environment with even greater precision. What did you miss at first glance? Pay attention to subtler details. Remember to use the RAW, Deductions, and Viewer Feelings tags appropriately."),
        ("Step 4: Subject's Mind (T4 - Basic)", "Excellent. Now enter the subject's inner world (Phase T4).\nPerform a Deep Mind Probe. Examine thoroughly: the subject's dominant emotions, vectors of their will, their strongest intentions, and their greatest fears or concerns. Do not create a story—provide clean data. Remember to use the RAW, Deductions, and Viewer Feelings tags."),
        ("Step 5: Deepening the Mind (T4 - Deepening)", "Excellent job reading the emotions.\nStay in T4 and go even deeper into the subject's mind. Look for what is hidden deepest beneath the first layer of emotions. What are the true foundations of their motivation? What lies at the very bottom of their psyche? Remember your formatting tags (RAW, Deductions, Viewer Feelings)."),
        ("Step 6: Body, Relations, and Numerical Profile (T5 - T7)", "Thank you, excellent reading. Let's move on.\n- Phase T5 (Body): Examine the subject's physical state, areas of tension, and overall energy level.\n- Phase T6 (Relationships): Identify the subject's most important relationship with another person, group, or structure. What emotions/influences flow between them?\n- Phase T7 (Numerical Profile): Evaluate the following indicators on a strict 0-6 scale, providing 1-2 RAW sentences explaining 'why' for each:\n  * T7Q1: Viewer's (your) trust in the subject\n  * T7Q2: Subject's genuine interest and engagement in what they are doing\n  * T7Q3: Subject's interest in the people around them\n  * T7Q4: Importance of the outcome of actions to the subject\n  * T7Q5: Subject's willingness to further invest time/effort/resources\n  * T7Q6: Subject's tolerance for risk"),
        ("Step 7: Awareness and Automated Questions (T8 - T9)", f"Outstanding! We are nearing the end.\n- Phase T8: Viewer Awareness and Light Up.\n  * T8A (Awareness): Focus on the relationship between yourself and the subject. Perceive if they register nothing at all (0), have a slight sense of being watched, or a strong impression of being observed (6). Map this on a 0-6 scale and record as 'T8A - viewer awareness: [number] + RAW description'.\n  * T8B (Light Up): For a brief moment, consciously increase the intensity of your attention on the subject. Perceive if an additional tension/twitch appears. Record as 'T8B - Light Up RAW'.\n\n- Phase T9: Answer the following questions directly from the field:\n{t9_questions}\n\nBased on the data gathered so far, formulate EXACTLY 2 of your own research questions that you consider most important in this investigation, ask them, and record the answers.")
    ]
    
    for title, prompt_text in prompts:
        st.session_state.messages.append({"role": "user", "content": prompt_text})
        reply = call_openrouter(st.session_state.api_key, st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        add_to_transcript(f"**{title}**\n\n{reply}\n\n---\n")
        transcript_placeholder.markdown(st.session_state.transcript)
    
    st.session_state.app_phase = "chat"
    st.rerun()

# --- INTERACTIVE CHAT PHASE (PAUSED AT T9) ---
if st.session_state.app_phase == "chat":
    st.success("✅ AI has completed base phases (T0-T9) and awaits further questions or a signal to end the session.")
    
    # Inject CSS for chat input (light blue background, larger font)
    st.markdown("""
    <style>
    div[data-testid="stChatInput"] textarea {
        background-color: #EBF5FB !important;
        border: 2px solid #3498DB !important;
        font-size: 18px !important;
        color: #1a1a1a !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #2874A6 !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        live_question = st.chat_input("Enter your questions for the target here...")
        if live_question:
            st.session_state.messages.append({"role": "user", "content": live_question})
            with st.spinner("AI ISBE is analyzing the field..."):
                reply = call_openrouter(st.session_state.api_key, st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                add_to_transcript(f"**Question (Live):** {live_question}\n\n**AI ISBE Response:**\n{reply}\n\n---\n")
                st.rerun()
                
    with col2:
        if st.button("🛑 END SESSION & REVEAL TARGET", use_container_width=True):
            st.session_state.app_phase = "running_t10"
            st.rerun()

# --- PHASE T10 (TELEPATHIC SUMMARY) ---
if st.session_state.app_phase == "running_t10":
    st.warning("Closing blind session (Generating Phase T10)...")
    t10_prompt = "That was a wonderful session, thank you very much!\nFinally, in Phase T10, gather the most important information regarding the subject's inner state and relationships in 3-7 short, raw sentences (RAW). Condense the data. Under no circumstances should you add new history or narrative."
    
    st.session_state.messages.append({"role": "user", "content": t10_prompt})
    reply = call_openrouter(st.session_state.api_key, st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    add_to_transcript(f"**Step 8: Telepathic Summary (T10)**\n\n{reply}\n\n=========================================\n")
    transcript_placeholder.markdown(st.session_state.transcript)
    
    st.session_state.app_phase = "reveal"
    st.rerun()

# --- TARGET REVEAL ---
if st.session_state.app_phase == "reveal":
    st.error("🔒 Blind session closed. Time for Feedback.")
    st.subheader("Target Reveal")
    
    # Inject CSS for target reveal area (light red background, larger font)
    st.markdown("""
    <style>
    div[data-testid="stTextArea"] textarea {
        background-color: #FDEDEC !important;
        border: 2px solid #E74C3C !important;
        font-size: 16px !important;
        color: #1a1a1a !important;
    }
    div[data-testid="stTextArea"] textarea::placeholder {
        color: #C0392B !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    placeholder_text = "Enter what the target was here.\nPlus: if you have photos, you can describe them in text format."
    
    real_target = st.text_area(
        label="Paste the target data below:", 
        placeholder=placeholder_text, 
        height=200
    )
    
    if st.button("Reveal Target & Generate Evaluation", type="primary"):
        if real_target:
            st.session_state.real_target = real_target
            st.session_state.app_phase = "evaluation"
            st.rerun()
        else:
            st.warning("Please enter the target description.")

# --- EVALUATION ---
if st.session_state.app_phase == "evaluation":
    st.info("Generating evaluation...")
    
    add_to_transcript(f"### ACTUAL TARGET REVEALED\n{st.session_state.real_target}\n\n---\n")
    transcript_placeholder.markdown(st.session_state.transcript)
    
    eval_prompt = f"PHASE 5: FEEDBACK AND EVALUATION\n\nThe blind session (Telepathy) is now over. I am providing you with the actual target data for feedback.\nThe real target hidden under ID {st.session_state.target_id} was:\n\n=== TARGET FILE CONTENT ===\n{st.session_state.real_target}\n===========================\n\nEvaluate your session in terms of subject exploration. What did you read flawlessly (emotions, motivations, relationships)? What was distorted? Remember - do not retroactively change your readings, just draw logical conclusions for future learning."
    
    st.session_state.messages.append({"role": "user", "content": eval_prompt})
    reply = call_openrouter(st.session_state.api_key, st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    
    add_to_transcript(f"**AI Evaluation (Feedback)**\n\n{reply}")
    transcript_placeholder.markdown(st.session_state.transcript)
    
    # Initialize variable for post-session questions
    st.session_state.post_questions_count = 0
    st.session_state.app_phase = "post_reveal_chat"
    st.rerun()

# --- POST-REVEAL CHAT (Conversation with Nemo - Max 5 questions) ---
if st.session_state.app_phase == "post_reveal_chat":
    st.success("✅ AI has completed the evaluation. You can now download the session or ask up to 5 questions about the target.")
    
    # Inject CSS for the final question input (Optional green/gray styling)
    st.markdown("""
    <style>
    div[data-testid="stChatInput"] textarea {
        background-color: #E9F7EF !important;
        border: 2px solid #27AE60 !important;
        font-size: 18px !important;
        color: #1a1a1a !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #1E8449 !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.session_state.post_questions_count < 5:
            post_q = st.chat_input(f"Ask Nemo about the target (Question {st.session_state.post_questions_count + 1}/5)...")
            if post_q:
                st.session_state.post_questions_count += 1
                st.session_state.messages.append({"role": "user", "content": post_q})
                with st.spinner("Nemo is analyzing the feedback..."):
                    reply = call_openrouter(st.session_state.api_key, st.session_state.messages)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    add_to_transcript(f"**Post-Session Question {st.session_state.post_questions_count}/5:** {post_q}\n\n**Nemo Response:**\n{reply}\n\n---\n")
                    st.rerun()
        else:
            st.info("You have reached the maximum of 5 post-session questions.")
            
    with col2:
        if st.button("🏁 FINISH & SAVE SESSION", use_container_width=True, type="primary"):
            st.session_state.app_phase = "finished"
            st.rerun()

# --- ENDING & DOWNLOAD ---
if st.session_state.app_phase == "finished":
    st.success("Session completely finished. Thank you and have a great day!")
    
    st.download_button(
        label="📥 Download session as .txt file",
        data=st.session_state.transcript,
        file_name=f"RV_Telepathy_{st.session_state.target_id}.txt",
        mime="text/plain",
        use_container_width=True
    )
    
    if st.button("🔄 Reset and start a new session", use_container_width=True):
        st.session_state.app_phase = "setup"
        st.session_state.transcript = ""
        st.session_state.messages = []
        st.session_state.target_id = generate_target_id()
        st.session_state.custom_t9 = ""
        st.session_state.post_questions_count = 0
        st.rerun()
