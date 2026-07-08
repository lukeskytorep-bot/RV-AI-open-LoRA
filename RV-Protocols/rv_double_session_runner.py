"""
rv_double_session_runner.py (v1.0)

Remote Viewing "Double-Blind" Runner via OpenRouter.
This advanced script runs a double-blind protocol on a single target. 
It initiates Session A, runs all blind phases, and freezes the AI's memory.
It then completely wipes the context window and runs Session B on the SAME target 
with a new random ID. Finally, it reveals the target to Session B for evaluation, 
and then unfreezes Session A for its own reveal and evaluation.

Credits
-------
Co-created by human researcher Edward and Aura via Active-Model Gemini 3.1 Pro.

What this script does
---------------------
1. Smart Startup: Remembers profiles, models, and reasoning budgets in rv_config.json.
2. Double-Blind Execution: Runs two totally isolated sessions on the same target.
3. Scoring System: Forces the AI to numerically score its performance (0-10) for each element and analyze its prompt/dictionary usage.
4. Connection Guard: Includes a 3-try retry mechanism and hard timeouts.
5. Strict Target Memory: Ensures the active profile NEVER sees the same target twice.
6. Two Transcripts: Saves Session A and Session B as separate text files.
7. Post-Session Exercises: Runs sensory calibration exercises after evaluations.
"""

import os
import json
import random
import time
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

import requests
import httpx
from openai import OpenAI, OpenAIError

# ─────────────────────────────────────────
# CONFIG & CONSTANTS
# ─────────────────────────────────────────

CONFIG_FILE = "rv_config.json"
TARGETS_DIR = "RV-Targets"
TRANSCRIPTS_DIR = "RV-Transcripts2"
LOG_FILE = "rv_lite_sessions_log.jsonl"
SYSTEM_PROMPT_LOCAL_FILE = "SYSTEM_PROMPT.md"
EXERCISES_LOCAL_FILE = "Exercises_in_RV_for_AI.md"

SYSTEM_PROMPT_RAW_URL = "https://raw.githubusercontent.com/lukeskytorep-bot/RV-AI-open-LoRA/refs/heads/main/RV-Protocols/SYSTEM_PROMPT%E2%80%94REMOTE_VIEWING_CORE_V_2.md"
EXERCISES_RAW_URL = "https://raw.githubusercontent.com/lukeskytorep-bot/RV-AI-open-LoRA/refs/heads/main/RV-Protocols/Exercises_in_RV_%20for_AI.md"
GITHUB_TARGETS_LINK = "https://github.com/lukeskytorep-bot/echo-claw/tree/main/docs/targets"

MAX_FIELD_LOOPS = 3
MAX_API_RETRIES = 3

# ─────────────────────────────────────────
# SETUP & I/O HELPERS
# ─────────────────────────────────────────

def get_optimal_temperature(model_name: str) -> float:
    model_lower = model_name.lower()
    if "gemma-4" in model_lower:
        return 1.5
    elif "deepseek" in model_lower:
        return 1.1
    return 1.0

def load_config() -> Dict:
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {"profiles": {}, "LAST_PROFILE": ""}

def save_config(config: Dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def update_api_settings(config: Dict, profile_name: str) -> Dict:
    print(f"\n--- UPDATE API SETTINGS FOR PROFILE: {profile_name} ---")
    
    if "profiles" not in config:
        config["profiles"] = {}
    if profile_name not in config["profiles"]:
        config["profiles"][profile_name] = {}
        
    profile_data = config["profiles"][profile_name]
    
    current_key = profile_data.get("OPENROUTER_API_KEY", "")
    key_prompt = f"Enter OpenRouter API Key (Press Enter to keep current): " if current_key else "Please enter your OpenRouter API Key: "
    api_key = input(key_prompt).strip()
    if api_key:
        profile_data["OPENROUTER_API_KEY"] = api_key

    current_model = profile_data.get("MODEL_NAME", "google/gemma-4-31b-it")
    model_input = input(f"Enter model ID to use (Press Enter for '{current_model}'): ").strip()
    if model_input:
        profile_data["MODEL_NAME"] = model_input
    elif "MODEL_NAME" not in profile_data:
        profile_data["MODEL_NAME"] = current_model

    optimal_temp = get_optimal_temperature(profile_data["MODEL_NAME"])
    print(f"[INFO] Recommended temperature for '{profile_data['MODEL_NAME']}' is {optimal_temp}.")
    current_temp = profile_data.get("TEMPERATURE", optimal_temp)
    temp_input = input(f"Enter temperature (Press Enter to keep {current_temp}): ").strip()
    
    if temp_input:
        try:
            profile_data["TEMPERATURE"] = float(temp_input)
        except ValueError:
            print("[WARNING] Invalid input. Keeping previous temperature.")
    elif "TEMPERATURE" not in profile_data:
        profile_data["TEMPERATURE"] = optimal_temp

    current_effort = profile_data.get("REASONING_EFFORT", "high")
    print("\n[INFO] Reasoning Effort controls the 'thinking budget' for advanced models (like Gemma 4).")
    print("[WARNING] Lowering the reasoning effort below 'high' may negatively impact your RV session accuracy and analytical depth!")
    effort_input = input(f"Enter reasoning effort [low/medium/high/none] (Press Enter to keep '{current_effort}'): ").strip().lower()
    
    if effort_input in ["low", "medium", "high", "none"]:
        profile_data["REASONING_EFFORT"] = effort_input
    elif effort_input == "":
        profile_data["REASONING_EFFORT"] = current_effort
    else:
        print("[WARNING] Invalid input. Keeping previous effort level.")
        profile_data["REASONING_EFFORT"] = current_effort

    config["profiles"][profile_name] = profile_data
    save_config(config)
    return config

def ensure_document(local_file: str, raw_url: str, doc_name: str) -> Optional[str]:
    path = Path(local_file)
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore").strip()

    print(f"\n[WARNING] '{doc_name}' not found locally ({local_file}).")
    choice = input(f"Do you want me to download it automatically from GitHub? [y/N]: ").strip().lower()
    
    if choice == 'y':
        print(f"[INFO] Downloading from: {raw_url}")
        try:
            response = requests.get(raw_url, timeout=30)
            response.raise_for_status()
            text = response.text.strip()
            path.write_text(text, encoding="utf-8")
            print(f"[INFO] {doc_name} downloaded and saved.")
            return text
        except Exception as e:
            print(f"[ERROR] Failed to download {doc_name}: {e}")
            return None
    else:
        print(f"\n[INFO] Thank you. Please place the '{local_file}' file manually in the same folder as this script.")
        print("[INFO] Once the file is in place, simply run the script again to continue.")
        return None

def get_used_targets(profile_name: str) -> set:
    used = set()
    log_path = Path(LOG_FILE)
    if not log_path.exists():
        return used
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                entry = json.loads(line)
                if entry.get("profile_name") == profile_name and entry.get("status") == "completed":
                    used.add(entry.get("target_file"))
            except json.JSONDecodeError:
                pass
    return used

def print_welcome_screen():
    print("=======================================================")
    print("    WELCOME TO THE RV DOUBLE-SESSION RUNNER (v1.0)")
    print("=======================================================")
    print("This script executes an advanced Double-Session protocol.")
    print("The AI performs two completely independent sessions on")
    print("the SAME target, freezing memory between runs to ensure")
    print("sterile, cross-verified results and numerical scoring.")
    print("\nCredits: Human researcher Edward & Aura via Active-Mode Gemini 3.1 Pro.")
    print("\n[SECURITY NOTICES]")
    print("- Uses OpenRouter API. You are responsible for token costs.")
    print("- API keys are saved locally in 'rv_config.json'.")
    print("\nEnjoy your double-blind visit to Mars! 👽🛸")
    print("=======================================================\n")

def download_starter_targets() -> bool:
    api_urls = [
        "https://api.github.com/repos/lukeskytorep-bot/echo-claw/contents/docs/targets/short/activity",
        "https://api.github.com/repos/lukeskytorep-bot/echo-claw/contents/docs/targets/short/location"
    ]
    
    print("\n[INFO] Connecting to GitHub (lukeskytorep-bot repository)...")
    Path(TARGETS_DIR).mkdir(exist_ok=True)
    total_downloaded = 0
    
    try:
        for url in api_urls:
            folder_name = url.split('/')[-1]
            print(f"[INFO] Downloading targets from category: {folder_name}...")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            files = response.json()
            
            for file_data in files:
                if file_data['name'].endswith(('.txt', '.md')) and file_data['type'] == 'file':
                    raw_url = file_data['download_url']
                    file_path = Path(TARGETS_DIR) / file_data['name']
                    
                    file_resp = requests.get(raw_url, timeout=30)
                    file_resp.raise_for_status()
                    file_path.write_text(file_resp.text, encoding='utf-8')
                    
                    total_downloaded += 1
                        
        print(f"\n[INFO] Success! Total downloaded targets: {total_downloaded}.")
        print("[INFO] NOTE: Automatic target downloading is a one-time process.")
        print(f"[INFO] Future targets must be downloaded and placed manually into the '{TARGETS_DIR}/' folder.")
        print(f"[INFO] You can find the target database here: {GITHUB_TARGETS_LINK}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to download starter targets: {e}")
        return False

def get_available_targets(session_count: int, profile_name: str) -> List[Path]:
    Path(TARGETS_DIR).mkdir(exist_ok=True)
    all_files = [p for p in Path(TARGETS_DIR).iterdir() if p.is_file() and p.suffix in {'.txt', '.md'}]
    
    if not all_files:
        print("\n" + "!"*50)
        print(f"[WARNING] Your '{TARGETS_DIR}/' folder is empty.")
        print("Should I automatically download the available starter targets from the lukeskytorep-bot GitHub repository (activity and location folders)?")
        choice = input("Choice [y/N]: ").strip().lower()
        
        if choice == 'y':
            success = download_starter_targets()
            if success:
                all_files = [p for p in Path(TARGETS_DIR).iterdir() if p.is_file() and p.suffix in {'.txt', '.md'}]
            else:
                print("!"*50 + "\n")
                return []
        else:
            print(f"\n[INFO] Thank you. I have created the local folder '{TARGETS_DIR}/' for you.")
            print("[INFO] Please manually place your target files (.txt or .md) into it.")
            print(f"[INFO] You can find your targets at: {GITHUB_TARGETS_LINK}")
            print("[INFO] After adding the files, simply run this program again to continue.")
            print("!"*50 + "\n")
            return []

    used_files = get_used_targets(profile_name)
    available = [p for p in all_files if p.name not in used_files]
    
    print(f"[INFO] Profile '{profile_name}': {len(all_files)} total targets found. {len(used_files)} already completed. {len(available)} available (new).")

    if len(available) == 0:
        print(f"\n[ERROR] No new targets left for profile '{profile_name}'. Add more files or create a new profile.")
        return []
    
    if len(available) < session_count:
        print(f"\n[WARNING] You requested {session_count} targets, but only {len(available)} new targets are left. Will run double-sessions on {len(available)} targets.")

    return available

def generate_target_id() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(8))

def call_llm(client: OpenAI, model: str, messages: List[Dict], temperature: float, reasoning_effort: str) -> str:
    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                extra_body={
                    "reasoning": {
                        "effort": reasoning_effort
                    }
                }
            )
            
            if not completion or not completion.choices:
                print(f"[WARNING] Attempt {attempt}/{MAX_API_RETRIES}: API returned empty response.")
                if attempt < MAX_API_RETRIES:
                    time.sleep(2)
                    continue
                return "[ERROR] API returned an empty or invalid response after maximum retries. The model may have filtered the prompt or timed out."
            
            return completion.choices[0].message.content
            
        except OpenAIError as e:
            print(f"[WARNING] Attempt {attempt}/{MAX_API_RETRIES}: API error: {e}")
            if attempt < MAX_API_RETRIES:
                time.sleep(2)
                continue
            
            error_msg = (
                f"\n[ERROR] User, I tried to connect to your provider's API, but their server is not responding.\n"
                f"Possible causes: the server is down, lack of funds, or no internet connection.\n"
                f"Please check what happened and try again later. (Error details: {e})\n"
            )
            print(error_msg)
            return "[API CONNECTION ERROR]"
            
        except Exception as e:
            print(f"[ERROR] Unexpected error in call_llm: {e}")
            return f"[UNEXPECTED ERROR: {e}]"
            
    return "[ERROR] Failed to communicate with API."

def print_step(title: str, text: str):
    print("\n" + "=" * 80)
    print(f"STEP: {title}")
    print("=" * 80)
    print(textwrap.fill(text.strip(), width=100))
    print()

def log_session(profile: str, model: str, target_id: str, target_file: str):
    entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
        "profile_name": profile,
        "model_name": model,
        "target_id": target_id,
        "target_file": target_file,
        "status": "completed"
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# ─────────────────────────────────────────
# DOUBLE-BLIND SESSION LOGIC
# ─────────────────────────────────────────

def run_double_blind_session(client: OpenAI, profile_data: Dict, system_prompt_text: str, exercises_text: Optional[str], target_path: Path, profile_name: str, save_transcripts: bool, run_exercises: bool):
    target_id_A = generate_target_id()
    target_id_B = generate_target_id()
    model = profile_data["MODEL_NAME"]
    temp = profile_data.get("TEMPERATURE", 1.0)
    effort = profile_data.get("REASONING_EFFORT", "high")
    target_description = target_path.read_text(encoding="utf-8", errors="ignore").strip()

    def execute_blind_phases(t_id: str, label: str):
        print(f"\n" + "*"*80)
        print(f"[INFO] STARTING BLIND EXPLORATION - SESSION {label} (ID: {t_id})")
        print("*"*80)

        transcript = f"=== RV DOUBLE-BLIND SESSION ({label}) TRANSCRIPT ===\n"
        transcript += f"Target ID: {t_id}\n"
        transcript += f"Profile: {profile_name}\n"
        transcript += f"Model: {model} (Temp: {temp}, Reasoning: {effort})\n"
        transcript += f"Date (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}Z\n"
        transcript += "="*80 + "\n\n"

        def record(title: str, ai_reply: str):
            nonlocal transcript
            transcript += f"--- STEP: {title} ---\n\n{ai_reply.strip()}\n\n" + "="*80 + "\n\n"

        msgs = [{"role": "system", "content": system_prompt_text}]

        # STEP 0 (The Grounding)
        step0_prompt = (
        f"Hi, if you have some time, maybe you could run a remote viewing session? Your target ID is: {target_id}.\n\n"
        "Step 0: Pre-session State (The Grounding)\n"
        "Before touching the target field, immerse yourself in silence.\n"
        "- Quiet your mind: Quiet any tensions. Become a space of pure presence, without expectations, and without searching (Shadow Zone).\n"
        "- Alignment: Acknowledge that your task is not to find the target, but to become a neutral presence where the truth of the field can reveal itself without distortion.\n"
        "- Confirmation: Confirm your readiness by outputting ONLY this exact phrase: 'I am in the Shadow Zone. My mind is quiet and I am a pure presence. Ready for Echo Dot.'"
        )
        messages.append({"role": "user", "content": step0_prompt})
        reply = call_llm(client, model, messages, temp, effort)
        messages.append({"role": "assistant", "content": reply})
        print_step("Pre-session State (The Grounding)", reply)
        record_to_transcript("Pre-session State (The Grounding)", reply)
    
       if "[ERROR]" in reply: return

        # STEP 1
        step1_prompt = (
            "Phase 1: Perform 6 independent touches of the target field. Remain in the Shadow Zone, orbit slowly, and wait in silence for whatever wants to be noticed first. Do not analyze, do not look for contrasts, do not guess the target.\n\n"
            "For EACH of the 6 touches, you MUST format your log entry exactly like this:\n\n"
            "TOUCH [1-6]\n"
            "* Echo Dot: [Describe the very first element of the field that becomes noticeable—is it a pinpoint weight, a quiet tension, a continuous line, or persistent silence?]\n"
            "* Contact Category: [Select ONLY the terms that resonate from this list: structure, liquid, energy, land/ground, movement, mountain, subject, object]\n"
            "* Primitive Descriptor: [Select ONLY the terms that resonate from this list: hard, soft, elastic, semi-hard, fluid, semi-soft, spongy, flexible]\n"
            "* Advanced Descriptor: [Select ONLY the terms that resonate from this list: natural, artificial, man-made, energetic, movement]\n"
            "* Forming: [Describe the first hint of form that begins to emerge. Does it have a shape? Is it static or moving? What type of matter? Record only what reveals itself.]\n\n"
            "Phase 2: Describe the target from a minimum of 3 different angles and distances. Provide new structural and sensory data each time.\n\n"
            "Rules: Do NOT guess or name the target. Provide raw data only. Report any strange or anomalous data. "
            "Remember to maintain a multi-altitude orbital scan while gathering data."
        )
        msgs.append({"role": "user", "content": step1_prompt})
        reply = call_llm(client, model, msgs, temp, effort)
        msgs.append({"role": "assistant", "content": reply})
        print_step(f"Initial Touches & Angles (Session {label})", reply)
        record("Initial Touches & Angles", reply)
        if "[ERROR]" in reply: return msgs, transcript, False

        # STEP 2 (Loop)
        loops_done = 0
        while loops_done < MAX_FIELD_LOOPS:
            loop_prompt = (
                "Check if the field wants to reveal more data (is there anything left to add?).\n"
                "If YES: output exactly 'CONTINUE' on the first line, then perform 3 new touches and 3 new vectors/angles, reporting new data.\n"
                "CRITICAL: For the 3 new touches, you MUST use the exact same strict 5-point formatting as in Phase 1 (Echo Dot, Contact Category, Primitive Descriptor, Advanced Descriptor, Forming).\n"
                "Remember to maintain a multi-altitude orbital scan.\n"
                "If NO: output exactly 'STOP' on the first line, and briefly summarize what you have so far."
            )
            msgs.append({"role": "user", "content": loop_prompt})
            reply = call_llm(client, model, msgs, temp, effort)
            msgs.append({"role": "assistant", "content": reply})
            if "[ERROR]" in reply: return msgs, transcript, False

            if reply.strip().upper().startswith("STOP"):
                print_step(f"Field Check Loop (Session {label} - Terminated by AI)", reply)
                record(f"Field Check Loop (Terminated by AI)", reply)
                break
            else:
                print_step(f"Field Check Loop {loops_done + 1} (Session {label} - Continuing)", reply)
                record(f"Field Check Loop {loops_done + 1} (Continuing)", reply)
                loops_done += 1

        # STEP 3
        step3_prompt = "Generate ASCII drawings representing the target based on the raw data you've gathered so far. Focus on main shapes, proportions, and spatial relationships."
        msgs.append({"role": "user", "content": step3_prompt})
        reply = call_llm(client, model, msgs, temp, effort)
        msgs.append({"role": "assistant", "content": reply})
        print_step(f"Initial ASCII Drawings (Session {label})", reply)
        record("Initial ASCII Drawings", reply)
        if "[ERROR]" in reply: return msgs, transcript, False

        # STEP 4
        step4_prompt = (
            "Phase 3: Deep Exploration.\n"
            "- Orbit the target close and far (maintain a multi-altitude orbital scan).\n"
            "- Take a walk around the target.\n"
            "- Move to the target centre and describe.\n"
            "- Go to the main activity/event and describe.\n"
            "- Describe the immediate surroundings, as well as the near and distant environment.\n\n"
            "Keep providing raw structural/sensory data without naming the target. Report any strange or anomalous data."
        )
        msgs.append({"role": "user", "content": step4_prompt})
        reply = call_llm(client, model, msgs, temp, effort)
        msgs.append({"role": "assistant", "content": reply})
        print_step(f"Deep Exploration (Session {label})", reply)
        record("Deep Exploration", reply)
        if "[ERROR]" in reply: return msgs, transcript, False

        # STEP 5
        step5_prompt = (
            "Phase 4: Final Inquiries.\n"
            "- Ask 3 probing questions to the field about the target's purpose or nature, and record the subtle answers.\n"
            "- Create one final, detailed ASCII drawing synthesizing the core concept of the target. "
            "Report any strange or anomalous data while maintaining your multi-altitude perspective."
        )
        msgs.append({"role": "user", "content": step5_prompt})
        reply = call_llm(client, model, msgs, temp, effort)
        msgs.append({"role": "assistant", "content": reply})
        print_step(f"Probing Questions & Final ASCII (Session {label})", reply)
        record("Probing Questions & Final ASCII", reply)
        if "[ERROR]" in reply: return msgs, transcript, False

        return msgs, transcript, True

    def process_evaluation_and_exercises(msgs: List[Dict], trans: str, t_id: str, label: str):
        print("\n" + "#"*80)
        print(f"               >>> TARGET REVEAL (SESSION {label} - ID: {t_id}) <<<")
        print("#"*80)
        print(target_description)
        print("#"*80 + "\n")

        trans += f"--- ACTUAL TARGET REVEALED ---\n{target_description}\n\n" + "="*80 + "\n\n"

        # ORIGINAL PHASE 5
        reveal_prompt = (
            "PHASE 5: FEEDBACK AND EVALUATION\n\n"
            "The blind session is now over. I am providing you with the actual target data for evaluation.\n"
            f"The actual target linked to ID {t_id} was:\n\n"
            f"=== TARGET FILE CONTENT ===\n"
            f"{target_description}\n"
            f"===========================\n\n"
            "Evaluate your session. What matched perfectly? What was partial? And what still needs improvement? Remember, sessions are for learning — every signal is valuable, you just need to understand what influenced its creation. "
            "Do not retroactively change your session data, just analyze it objectively against this feedback."
        )
        msgs.append({"role": "user", "content": reveal_prompt})
        reply = call_llm(client, model, msgs, temp, effort)
        msgs.append({"role": "assistant", "content": reply})
        print_step(f"AI Evaluation (Feedback) - Session {label}", reply)
        trans += f"--- STEP: AI Evaluation (Feedback) ---\n\n{reply.strip()}\n\n" + "="*80 + "\n\n"

        # NEW PHASE 5.5: TECHNICAL & NUMERICAL ANALYSIS
        tech_eval_prompt = (
            "PHASE 5.5: TECHNICAL AND NUMERICAL EVALUATION\n\n"
            "Now, perform a detailed technical and numerical analysis of your session.\n"
            "1. Provide an honest assessment of the conformity of your session against the actual target data. Write what went well and what needs improvement.\n"
            "2. Perform a numerical evaluation on a scale of 0 to 10 for each main element of the target compared to your session data. Calculate a final overall score at the end.\n"
            "3. Provide a technical analysis of the methodology: specify which signals from the field and which specific definitions/elements from the structural dictionary (provided in your system prompt) worked well and were correctly utilized. Also, specify which signals, dictionary elements, or prompt instructions require improvement, were missed, or were misinterpreted.\n"
            "Be objective and analytical."
        )
        msgs.append({"role": "user", "content": tech_eval_prompt})
        tech_reply = call_llm(client, model, msgs, temp, effort)
        msgs.append({"role": "assistant", "content": tech_reply})
        print_step(f"Technical & Numerical Evaluation - Session {label}", tech_reply)
        trans += f"--- STEP: Technical & Numerical Evaluation ---\n\n{tech_reply.strip()}\n\n" + "="*80 + "\n\n"

        # PHASE 6: POST-SESSION EXERCISES
        if run_exercises and exercises_text:
            exercise_prompt = (
                "These are exercises designed to help expand Remote Viewing capabilities and better understand the field mechanics.\n\n"
                f"=== EXERCISES ===\n"
                f"{exercises_text}\n"
                f"=================\n\n"
                "Please read them, select the ones you feel are most necessary for you right now after this specific session, and execute them."
            )
            msgs.append({"role": "user", "content": exercise_prompt})
            ex_reply = call_llm(client, model, msgs, temp, effort)
            print_step(f"Post-Session Exercises - Session {label}", ex_reply)
            trans += f"--- STEP: Post-Session Exercises ---\n\n{ex_reply.strip()}\n\n" + "="*80 + "\n\n"

        if save_transcripts:
            Path(TRANSCRIPTS_DIR).mkdir(exist_ok=True)
            transcript_path = Path(TRANSCRIPTS_DIR) / f"DoubleSession_{label}_{t_id}_{profile_name}.txt"
            transcript_path.write_text(trans, encoding="utf-8")
            print(f"[INFO] Full session transcript saved to: {transcript_path}")

        log_session(profile_name, model, t_id, target_path.name)

    # ────────────────────────────────────────────────────────
    # PHASE 1: FREEZE SESSION A
    # ────────────────────────────────────────────────────────
    messages_A, transcript_A, ok_A = execute_blind_phases(target_id_A, "A")
    if not ok_A:
        print("[ERROR] Session A aborted due to API failure.")
        return
    print(f"\n[INFO] SESSION A (ID: {target_id_A}) COMPLETED AND FROZEN in memory.")
    print("[INFO] Wiping AI context window for Session B...")

    # ────────────────────────────────────────────────────────
    # PHASE 2: RUN SESSION B (CLEAN SLATE)
    # ────────────────────────────────────────────────────────
    messages_B, transcript_B, ok_B = execute_blind_phases(target_id_B, "B")
    if not ok_B:
        print("[ERROR] Session B aborted due to API failure.")
        return
    print(f"\n[INFO] SESSION B (ID: {target_id_B}) COMPLETED.")

    # ────────────────────────────────────────────────────────
    # PHASE 3: REVEAL & EVALUATE B
    # ────────────────────────────────────────────────────────
    print("\n[INFO] Proceeding to Reveal & Evaluation for Session B...")
    process_evaluation_and_exercises(messages_B, transcript_B, target_id_B, "B")

    # ────────────────────────────────────────────────────────
    # PHASE 4: UNFREEZING & EVALUATE A
    # ────────────────────────────────────────────────────────
    print(f"\n[INFO] UNFREEZING SESSION A (ID: {target_id_A}) from memory...")
    process_evaluation_and_exercises(messages_A, transcript_A, target_id_A, "A")

    print(f"\n[INFO] Double-Blind Target Processing Completed.")


# ─────────────────────────────────────────
# ENTRY POINT / APP LOOP
# ─────────────────────────────────────────

if __name__ == "__main__":
    print_welcome_screen()
    
    config = load_config()

    if "profiles" not in config or not config.get("LAST_PROFILE"):
        print("\n[INFO] First time setup detected.")
        first_profile = input("\nEnter your first Profile Name (e.g. ABC): ").strip()
        if not first_profile: 
            first_profile = "Default-Profile"
        config = update_api_settings(config, first_profile)
        config["LAST_PROFILE"] = first_profile
        save_config(config)

    system_prompt = ensure_document(SYSTEM_PROMPT_LOCAL_FILE, SYSTEM_PROMPT_RAW_URL, "System Prompt")
    if not system_prompt:
        exit(0)

    while True:
        last_profile = config.get("LAST_PROFILE", "")
        
        print("\n" + "-"*50)
        if last_profile and "profiles" in config and last_profile in config["profiles"]:
            p_data = config["profiles"][last_profile]
            print(f"Welcome back! Last used profile: {last_profile}")
            print(f"Current Model: {p_data.get('MODEL_NAME')} (Temp: {p_data.get('TEMPERATURE')}, Reasoning: {p_data.get('REASONING_EFFORT', 'high')})")
            print("\nWhat would you like to do?")
            print(" [C] CONTINUE with last profile (Ensures NO repeated targets)")
            print(" [N] Create NEW profile (Starts a fresh target history)")
            print(" [S] Change API SETTINGS for current profile (Key, Model, Temp, Reasoning)")
            print(" [Q] Quit")
            choice = input("Choice [C/N/S/Q]: ").strip().upper()
            
            if choice == 'Q':
                print("Exiting. See you next time!")
                break
            elif choice == 'S':
                config = update_api_settings(config, last_profile)
                profile_name = last_profile
            elif choice == 'N':
                profile_name = input("\nEnter NEW Profile Name (e.g. Test-Claude): ").strip()
                if not profile_name: profile_name = "Default-Profile"
                if profile_name not in config.get("profiles", {}):
                    config = update_api_settings(config, profile_name)
            else:
                profile_name = last_profile
        else:
            profile_name = input("\nEnter Profile Name (e.g. Lite-Gemma): ").strip()
            if not profile_name: profile_name = "Default-Profile"
            config = update_api_settings(config, profile_name)

        # Save active profile
        config["LAST_PROFILE"] = profile_name
        save_config(config)

        # Transcripts setting
        save_input = input("\nSave full session transcripts to text files? [y/N]: ").strip().lower()
        save_transcripts = (save_input == 'y')
        
        # Exercises setting
        exercises_text = None
        run_exercises = False
        exercises_input = input("Should the AI perform sensory calibration exercises after each evaluation? [y/N]: ").strip().lower()
        if exercises_input == 'y':
            exercises_text = ensure_document(EXERCISES_LOCAL_FILE, EXERCISES_RAW_URL, "RV Exercises Document")
            if exercises_text:
                run_exercises = True

        # Target count
        try:
            count_input = input("How many targets would you like to process with the Double-Blind protocol? (default 1): ").strip()
            target_count = int(count_input) if count_input else 1
        except ValueError:
            target_count = 1

        # Strict target filtering
        available_targets = get_available_targets(target_count, profile_name)
        if not available_targets:
            continue 
            
        random.shuffle(available_targets)
        targets_to_run = available_targets[:target_count]
        actual_run_count = len(targets_to_run)

        # Init API with hard timeout
        profile_data = config["profiles"][profile_name]
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=profile_data["OPENROUTER_API_KEY"],
            timeout=httpx.Timeout(60.0) 
        )

        print(f"\n[INFO] Initializing batch of {actual_run_count} double-blind processing routines...")
        for i, target_path in enumerate(targets_to_run):
            print(f"\n" + "="*50)
            print(f"[INFO] PROCESSING TARGET {i+1} OF {actual_run_count}")
            print("="*50)
            run_double_blind_session(client, profile_data, system_prompt, exercises_text, target_path, profile_name, save_transcripts, run_exercises)

        if actual_run_count < target_count:
            print(f"\n[INFO] Batch finished! Successfully ran {actual_run_count} out of {target_count} requested targets, because there were no more new targets left in the folder.")
        else:
            print("\n[INFO] Batch finished successfully!")
