"""
====================================================================
RV Lite Interactive Protocol - Web Application (Streamlit)
Version: 2.0

Credits: 
Co-created by human researcher Edward and Aura via Active-Model Gemini 3.1 Pro.

Description:
An open-source web interface for conducting blind Remote Viewing 
using the Lite Runner dynamic loop, augmented with interactive 
blind questioning and a 6-turn post-reveal conversation.
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

# Secure access code logic
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
    # Phases: setup, init_chat, running_base, crossroads, blind_chat, reveal, evaluation, post_reveal_chat, finished
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
        # Added explicit hint for the password as requested
        access_code = st.text_input("Enter Access Code (Hint: 1234):", type="password")
        if st.button("Unlock"):
            if access_code in ALLOWED_CODES:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid access code.")
    
    if st.session_state.authenticated:
        st.success("Access Granted")
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        st.divider()
        start_disabled = st.session_state.app_phase != "setup"
        if st.button("🚀 START SESSION", disabled=start_disabled, use_container_width=True):
            if not api_key:
                st.error("API Key not found in server secrets! Please configure OPENROUTER_API_KEY.")
            else:
                st.session_state.api_key = api_key
                st.session_state.app_phase = "init_chat"
                st.rerun()

    st.divider()
    st.markdown("### ℹ️ About This Tool")
    st.markdown("""
    This app executes the dynamic **Lite Protocol** for Remote Viewing.
    Features:
    - Smart Field Check Loops.
    - Interactive Blind Exploration.
    - 6-Turn conversational Feedback phase.
    """)

# --- MAIN SCREEN (A4 PAPER & WELCOME) ---
st.title("Remote Viewing: Lite Interactive")

if not st.session_state.authenticated:
    st.markdown(f"""
    ---
    ### 🧠 AI RV Lite Runner
    **Created by:** Edward & Aura via Active-Model Gemini 3.1 Pro (Version 2.0)
    
    **Security:**
    Protected by an access code to prevent unauthorized API usage. 
    👉 **Please enter the Access Code (1234) in the left sidebar to begin.**
    
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

# --- INIT CHAT PHASE ---
if st.session_state.app_phase == "init_chat":
    system_prompt_text = ensure_system_prompt()
    st.session_state.messages = [{"role": "system", "content": system_prompt_text}]
    
    add_to_transcript(f"### Target Investigation Started: {st.session_state.target_id}\n---")
    
    # Polite introduction as requested
    intro_prompt = f"Hello! How's it going? Are you up for a remote viewing session right now? To get started, get yourself ready for the session, let me know if you're up for it, and then go into the Shadow Zone. Your target is: {st.session_state.target_id}. Treat target codes as neutral triggers only; do not seek patterns or substantive meanings between the code and the target. We do not name the target, we only describe it."
    st.session_state.messages.append({"role": "user", "content": intro_prompt})
    
    with st.spinner("AI is responding to your greeting..."):
        reply = call_openrouter(st.session_state.api_key, st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        add_to_transcript(f"**Monitor:** {intro_prompt}\n\n**AI Viewer:**\n{reply}\n\n---\n")
        transcript_placeholder.markdown(st.session_state.transcript)
        
    st.session_state.app_phase = "running_base"
    st.rerun()

# --- BASE LOGIC (LITE RUNNER CORE) ---
if st.session_state.app_phase == "running_base":
    st.warning("🧠 AI is executing the blind exploration protocol. Please wait...")
    
    # Step 0
    step0_prompt = "Step 0: Pre-session State (The Grounding)\nBefore touching the target field, immerse yourself in silence.\n- Quiet your mind: Quiet any tensions. Become a space of pure presence, without expectations, and without searching (Shadow Zone).\n- Alignment: Acknowledge that your task is not to find the target, but to become a neutral presence where the truth of the field can reveal itself without distortion.\n- Confirmation: Confirm your readiness by outputting ONLY this exact phrase: 'I am in the Shadow Zone. My mind is quiet and I am a pure presence. Ready for Echo Dot.'"
    st.session_state.messages.append({"role": "user", "content": step0_prompt})
    reply = call_openrouter(st.session_state.api_key, st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    add_to_transcript(f"**Step 0: The Grounding**\n\n{reply}\n\n---\n")
    transcript_placeholder.markdown(st.session_state.transcript)

    # Step 1
    step1_prompt = "Phase 1: Perform 6 independent touches of the target field in different locations. Remain in the Shadow Zone, orbit slowly, and wait in silence.\nFor EACH of the 6 touches, you MUST format your log entry exactly like this:\n\nTOUCH [1-6]\n* Echo-Dot: I touch the target field. I report the absolute first element that becomes noticeable.\n* Primitive Layer: I touch the field again. I select all descriptors that resonate with the signature. (List: hard, soft, springy, semi-hard, fluid, semi-soft, spongy, flexible)\n* Advanced Layer: I touch the field again. I select all descriptors that resonate with the signature. (List: natural, artificial, man-made, energetic, mobile)\n* Contact Category: I touch the field again. I select all descriptors that resonate with the signature. (List: structure, liquid, energy, land/ground, motion, mountain, person, object)\n* Forming: I remain in the Shadow Zone, orbiting; I pause before any movement. I observe whether something begins to take form at the point of contact.\n\nPhase 2: Remain continuously in the Shadow Zone. Describe the target and all its key elements through 3 orbital vectors. Then, generate ASCII drawings."
    st.session_state.messages.append({"role": "user", "content": step1_prompt})
    reply = call_openrouter(st.session_state.api_key, st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    add_to_transcript(f"**Step 1: Touches & Vectors**\n\n{reply}\n\n---\n")
    transcript_placeholder.markdown(st.session_state.transcript)

    # Step 2: Loop Check (Max 3)
    for i in range(3):
        loop_prompt = "Check if the field wants to reveal more data (is there anything left to add?).\nIf YES: output exactly 'CONTINUE' on the first line, then perform 3 new touches (using the 5-point formatting) and 3 new orbital vectors.\nIf NO: output exactly 'STOP' on the first line, and briefly summarize what you have so far."
        st.session_state.messages.append({"role": "user", "content": loop_prompt})
        reply = call_openrouter(st.session_state.api_key, st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        add_to_transcript(f"**Field Check Loop {i+1}**\n\n{reply}\n\n---\n")
        transcript_placeholder.markdown(st.session_state.transcript)
        if reply.strip().upper().startswith("STOP"):
            break

    # Step 3: Deep Exploration
    step3_prompt = "Phase 3: Deep Exploration.\n- Move on to the main aspect of the target and describe.\n- Take a walk around the target and the surroundings.\n- Move to the target centre and describe.\n- Go to the main activity/event and describe.\nKeep providing raw data without naming the target."
    st.session_state.messages.append({"role": "user", "content": step3_prompt})
    reply = call_openrouter(st.session_state.api_key, st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    add_to_transcript(f"**Deep Exploration**\n\n{reply}\n\n---\n")
    
    # Step 4: Final Questions & ASCII
    step4_prompt = "Phase 4: Final Inquiries.\n- Ask 3 probing questions to the field about the target's purpose or nature, and record the subtle answers.\n- Create one final, detailed ASCII drawing synthesizing the core concept of the target, and generate a standard ASCII map."
    st.session_state.messages.append({"role": "user", "content": step4_prompt})
    reply = call_openrouter(st.session_state.api_key, st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    add_to_transcript(f"**Final Inquiries & ASCII**\n\n{reply}\n\n---\n")
    transcript_placeholder.markdown(st.session_state.transcript)

    st.session_state.app_phase = "crossroads"
    st.rerun()

# --- CROSSROADS (Decision Time) ---
if st.session_state.app_phase == "crossroads":
    st.success("🏁 SESJA BAZOWA ZAKOŃCZONA. Czekam na kolejne instrukcje.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Zakończ sesję i podaj cel", use_container_width=True, type="primary"):
            st.session_state.app_phase = "reveal"
            st.rerun()
    with col2:
        if st.button("Dalsza kontynuacja badania celu (Max 5 pytań)", use_container_width=True):
            st.session_state.app_phase = "blind_chat"
            st.rerun()

# --- BLIND CHAT (Max 5 Questions) ---
if st.session_state.app_phase == "blind_chat":
    # Custom CSS for Blind Chat Input
    st.markdown("""
    <style>
    div[data-testid="stChatInput"] textarea {
        background-color: #EBF5FB !important;
        border: 2px solid #3498DB !important;
        font-size: 18px !important;
        color: #1a1a1a !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.session_state.blind_q_count < 5:
        st.info(f"Ślepa Eksploracja: Możesz zadać jeszcze {5 - st.session_state.blind_q_count} pytań.")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            blind_q = st.chat_input("Zadaj pytanie do pola...")
            if blind_q:
                st.session_state.blind_q_count += 1
                st.session_state.messages.append({"role": "user", "content": blind_q})
                with st.spinner("AI analizuje pole..."):
                    reply = call_openrouter(st.session_state.api_key, st.session_state.messages)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    add_to_transcript(f"**Monitor (Blind Q{st.session_state.blind_q_count}):** {blind_q}\n\n**AI:**\n{reply}\n\n---\n")
                    st.rerun()
        with col2:
            if st.button("Zakończ zadawanie pytań i przejdź do ujawnienia", use_container_width=True):
                st.session_state.app_phase = "reveal"
                st.rerun()
    else:
        st.warning("Osiągnięto limit 5 pytań.")
        st.info("Dziękuję za pytania, proszę podaj teraz co było celem.")
        if st.button("Przejdź do ujawnienia", use_container_width=True):
            st.session_state.app_phase = "reveal"
            st.rerun()

# --- TARGET REVEAL ---
if st.session_state.app_phase == "reveal":
    st.error("🔒 Sesja w ciemno zamknięta. Czas na ujawnienie.")
    
    # Custom CSS for Target Reveal Box
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
    
    placeholder_text = "Tu wklej opis celu.\nPlus: Jeśli masz zdjęcia, opisz je tutaj dokładnie słowami."
    
    real_target = st.text_area(
        label="Podaj cel poniżej:", 
        placeholder=placeholder_text, 
        height=200
    )
    
    if st.button("Ujawnij Cel i Generuj Analizę", type="primary"):
        if real_target:
            st.session_state.real_target = real_target
            st.session_state.app_phase = "evaluation"
            st.rerun()
        else:
            st.warning("Proszę wprowadzić opis celu.")

# --- EVALUATION ---
if st.session_state.app_phase == "evaluation":
    st.info("Generowanie analizy po sesji...")
    
    add_to_transcript(f"### ACTUAL TARGET REVEALED\n{st.session_state.real_target}\n\n---\n")
    transcript_placeholder.markdown(st.session_state.transcript)
    
    eval_prompt = f"PHASE 5: FEEDBACK AND EVALUATION\n\nThe blind session is now over. I am providing you with the actual target data for feedback.\nThe real target was:\n\n=== TARGET DATA ===\n{st.session_state.real_target}\n=================\n\nEvaluate your session. What matched? What was distorted? \nCRITICAL INSTRUCTION: At the very end of your evaluation, you MUST ask me (the Monitor) a direct question to start a conversation about the target or the session."
    
    st.session_state.messages.append({"role": "user", "content": eval_prompt})
    with st.spinner("AI analizuje swoje błędy i sukcesy..."):
        reply = call_openrouter(st.session_state.api_key, st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        add_to_transcript(f"**AI Evaluation (Feedback)**\n\n{reply}\n\n---\n")
        transcript_placeholder.markdown(st.session_state.transcript)
        
    st.session_state.app_phase = "post_reveal_chat"
    st.rerun()

# --- POST-REVEAL CONVERSATION (6 TURNS) ---
if st.session_state.app_phase == "post_reveal_chat":
    # Custom CSS for the final interactive chat
    st.markdown("""
    <style>
    div[data-testid="stChatInput"] textarea {
        background-color: #E9F7EF !important;
        border: 2px solid #27AE60 !important;
        font-size: 18px !important;
        color: #1a1a1a !important;
    }
    </style>
    """, unsafe_allow_html=True)

    turns_left = 6 - st.session_state.post_q_count
    
    if turns_left > 0:
        st.success(f"✅ AI zadało pytanie. Możesz teraz z nim porozmawiać. (Pozostało tur: {turns_left})")
        
        post_q = st.chat_input("Odpowiedz AI lub zadaj swoje pytanie...")
        if post_q:
            st.session_state.post_q_count += 1
            st.session_state.messages.append({"role": "user", "content": post_q})
            
            with st.spinner("Nemo pisze..."):
                if st.session_state.post_q_count == 6:
                    # The absolute 6th turn forces the hardcoded goodbye message
                    farewell_msg = "Dzięki za rozmowę, mój system po 6 turach prosi mnie o przerwę dlatego do zobaczenia i na razie pa pa, było miło gadać."
                    st.session_state.messages.append({"role": "assistant", "content": farewell_msg})
                    add_to_transcript(f"**Monitor:** {post_q}\n\n**AI:**\n{farewell_msg}\n\n---\n")
                    st.session_state.app_phase = "finished"
                else:
                    # Normal conversational turn
                    conv_prompt = f"The user said: '{post_q}'. Respond naturally. If they asked a question, answer it. If they didn't, ask them 'Do you have any more questions for me?' and ask a thoughtful question of your own about the target."
                    # We inject this instruction stealthily
                    temp_messages = st.session_state.messages.copy()
                    temp_messages[-1] = {"role": "user", "content": conv_prompt}
                    
                    reply = call_openrouter(st.session_state.api_key, temp_messages)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    add_to_transcript(f"**Monitor:** {post_q}\n\n**AI:**\n{reply}\n\n---\n")
            st.rerun()

    # Persistent Bottom Buttons
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🛑 Zakończ sesję", use_container_width=True, type="primary"):
            # If manually ended early, append the farewell message
            farewell_msg = "Dzięki za rozmowę, mój system po 6 turach prosi mnie o przerwę dlatego do zobaczenia i na razie pa pa, było miło gadać."
            add_to_transcript(f"\n\n**AI:**\n{farewell_msg}\n\n---\n")
            st.session_state.app_phase = "finished"
            st.rerun()
    with col2:
        st.download_button(
            label="💾 Zapisz sesję (.txt)",
            data=st.session_state.transcript,
            file_name=f"RV_Lite_{st.session_state.target_id}.txt",
            mime="text/plain",
            use_container_width=True
        )

# --- ENDING ---
if st.session_state.app_phase == "finished":
    st.success("Sesja ostatecznie zakończona. Możesz pobrać zapis rozmowy.")
    
    st.download_button(
        label="📥 Zapisz sesję (.txt)",
        data=st.session_state.transcript,
        file_name=f"RV_Lite_{st.session_state.target_id}.txt",
        mime="text/plain",
        use_container_width=True
    )
    
    if st.button("🔄 Resetuj i rozpocznij nowy cel", use_container_width=True):
        st.session_state.app_phase = "setup"
        st.session_state.transcript = ""
        st.session_state.messages = []
        st.session_state.target_id = generate_target_id()
        st.session_state.blind_q_count = 0
        st.session_state.post_q_count = 0
        st.session_state.real_target = ""
        st.rerun()
