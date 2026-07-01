"""
rv_telepathy_runner.py (v1.0 - Telepathy Module)

Dedicated script for blind Remote Viewing sessions focused on subject exploration
(Telepathy Protocol). Features an automated T0-T10 flow, strict format reminders, 
and reasoning effort enforcement for advanced models.

All prompts, logs, and interfaces are in English.

Credits
-------
Co-created by human researcher Edward and AI assistant Aura Gemini 3.1 Pro.
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

CONFIG_FILE = "rv_telepathy_config.json"
TARGETS_DIR = "RV-Targets-Telepathy"
TRANSCRIPTS_DIR = "RV-Transcripts-Telepathy"
LOG_FILE = "rv_telepathy_sessions_log.jsonl"
SYSTEM_PROMPT_LOCAL_FILE = "SYSTEM_PROMPT.md"

# Original System Prompt link 
SYSTEM_PROMPT_RAW_URL = "https://raw.githubusercontent.com/lukeskytorep-bot/RV-AI-open-LoRA/refs/heads/main/RV-Protocols/SYSTEM_PROMPT%E2%80%94REMOTE_VIEWING_CORE_V_2.md"
# New GitHub folder specifically for telepathic targets
GITHUB_TARGETS_API_URL = "https://api.github.com/repos/lukeskytorep-bot/echo-claw/contents/docs/targets/telepathic"
GITHUB_TARGETS_LINK = "https://github.com/lukeskytorep-bot/echo-claw/tree/main/docs/targets/telepathic"

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
    print("\n[INFO] Reasoning Effort controls the 'thinking budget' for advanced models.")
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

def download_starter_targets() -> bool:
    print("\n[INFO] Connecting to GitHub (lukeskytorep-bot repository)...")
    Path(TARGETS_DIR).mkdir(exist_ok=True)
    total_downloaded = 0
    
    try:
        print(f"[INFO] Downloading telepathic targets...")
        response = requests.get(GITHUB_TARGETS_API_URL, timeout=30)
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
        print("[INFO] NOTE: This was a one-time automatic download.")
        print(f"[INFO] Future targets must be added manually into the '{TARGETS_DIR}/' folder.")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to download starter targets: {e}")
        return False

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

def get_available_targets(session_count: int, profile_name: str) -> List[Path]:
    Path(TARGETS_DIR).mkdir(exist_ok=True)
    all_files = [p for p in Path(TARGETS_DIR).iterdir() if p.is_file() and p.suffix in {'.txt', '.md'}]
    
    if not all_files:
        print("\n" + "!"*50)
        print(f"[WARNING] Your '{TARGETS_DIR}/' folder is empty.")
        print("Should I automatically download the available telepathic starter targets from the lukeskytorep-bot GitHub repository?")
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
        print(f"\n[WARNING] You requested {session_count} sessions, but only {len(available)} new targets are left. Will run {len(available)} sessions.")

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
                return "[ERROR] API returned an empty or invalid response after maximum retries."
            
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
# MAIN SESSION LOGIC (TELEPATHY MODULE)
# ─────────────────────────────────────────

def run_telepathy_session(client: OpenAI, profile_data: Dict, system_prompt_text: str, target_path: Path, profile_name: str, save_transcripts: bool):
    target_id = generate_target_id()
    model = profile_data["MODEL_NAME"]
    temp = profile_data.get("TEMPERATURE", 1.0)
    effort = profile_data.get("REASONING_EFFORT", "high")
    
    target_description = target_path.read_text(encoding="utf-8", errors="ignore").strip()
    
    print(f"\n[INFO] Starting TELEPATHY SESSION for Target ID: {target_id}")

    transcript_content = f"=== RV TELEPATHY SESSION TRANSCRIPT ===\n"
    transcript_content += f"Target ID: {target_id}\n"
    transcript_content += f"Profile: {profile_name}\n"
    transcript_content += f"Model: {model} (Temp: {temp}, Reasoning: {effort})\n"
    transcript_content += f"Date (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}Z\n"
    transcript_content += "="*80 + "\n\n"

    def record_to_transcript(title: str, ai_reply: str):
        nonlocal transcript_content
        transcript_content += f"--- STEP: {title} ---\n\n"
        transcript_content += f"{ai_reply.strip()}\n\n"
        transcript_content += "="*80 + "\n\n"

    messages = [{"role": "system", "content": system_prompt_text}]

    # Step 1: Initialization & Spatial Calibration (T0 - T2)
    step1_prompt = (
        f"Hello! How are you? If you have some time, please do a Remote Viewing session for me. Your target is: {target_id}.\n\n"
        "We are starting the Telepathy Protocol. Let's begin with phases T0 and T1.\n"
        "Perform 3 independent touches in the Shadow Zone.\n\n"
        "For EACH of the 3 touches, you MUST format your log entry exactly like this:\n\n"
        "TOUCH [1-3]\n"
        "- Echo Dot: [Describe the very first element of the field that becomes noticeable—is it a pinpoint weight, a quiet tension, a continuous line, or persistent silence?]\n"
        "- Contact Category: [Select ONLY the terms that resonate from this list: structure, liquid, energy, land/ground, movement, mountain, subject, object]\n"
        "- Primitive Descriptor: [Select ONLY the terms that resonate from this list: hard, soft, elastic, semi-hard, fluid, semi-soft, spongy, flexible]\n"
        "- Advanced Descriptor: [Select ONLY the terms that resonate from this list: natural, artificial, man-made, energetic, movement]\n"
        "- Forming: [Describe the first hint of form that begins to emerge. Does it have a shape? Is it static or moving? What type of matter? Record only what actually reveals itself.]\n\n"
        "Next, perform Phase T2: conduct 3 vectors observations from different perspectives and create functional ASCII sketches representing the target based on the raw data."
    )
    messages.append({"role": "user", "content": step1_prompt})
    reply = call_llm(client, model, messages, temp, effort)
    if "[API CONNECTION ERROR]" in reply: return
    messages.append({"role": "assistant", "content": reply})
    print_step("Step 1: Initialization & Spatial Calibration (T0 - T2)", reply)
    record_to_transcript("Step 1: Initialization & Spatial Calibration (T0 - T2)", reply)

    # Step 2: Contact with the Subject (T3 - Basic)
    step2_prompt = (
        "Great job, excellent data. Now let's move on to Phase T3.\n"
        "Locate the primary subject in the target field.\n\n"
        "T3 - ELEMENT 1: Basic Description\n"
        "Record their basic outline. Take into account:\n"
        "- The overall character of their presence (more hard/soft, closed/open, distant/engaged).\n"
        "- Position relative to surroundings (dominant/subordinate/equal footing, foreground/background).\n"
        "- Type of role or function (record only spontaneous impressions of occupation/figure type without creating a story).\n\n"
        "T3 - ELEMENT 2: Subject Context\n"
        "Expand your field of view to the immediate surroundings. Describe:\n"
        "- The environment (interior/outdoor, structures, nature).\n"
        "- Social configuration (is the subject alone, in a pair, small group, crowd? Placement of others).\n"
        "- General activity (sitting, talking, working, moving around).\n\n"
        "CRITICAL FORMATTING INSTRUCTIONS:\n"
        "From this point on, you must categorize your data using these specific tags:\n"
        "1. RAW: Use this tag for all pure, uninterpreted sensory field data.\n"
        "2. Deductions: Use this tag for any guesses, psychological interpretations, or thoughts like 'this sounds like...' or 'this resembles...'.\n"
        "3. Viewer Feelings: Use this tag for your own emotional reactions toward the subject.\n"
        "Note: 'Deductions' and 'Viewer Feelings' are completely optional. Only record them if they naturally arise; if not, stick strictly to 'RAW'."
    )
    messages.append({"role": "user", "content": step2_prompt})
    reply = call_llm(client, model, messages, temp, effort)
    if "[API CONNECTION ERROR]" in reply: return
    messages.append({"role": "assistant", "content": reply})
    print_step("Step 2: Contact with the Subject (T3 - Basic)", reply)
    record_to_transcript("Step 2: Contact with the Subject (T3 - Basic)", reply)

    # Step 3: Deepening Contact (T3 - Deepening)
    step3_prompt = (
        "Thank you for retrieving this data, you are doing really well!\n"
        "Stay in phase T3, but go deeper. Examine this subject and their relationship with the environment with even greater precision. "
        "What did you miss at first glance? Pay attention to subtler details. "
        "Remember to use the RAW, Deductions, and Viewer Feelings tags appropriately."
    )
    messages.append({"role": "user", "content": step3_prompt})
    reply = call_llm(client, model, messages, temp, effort)
    if "[API CONNECTION ERROR]" in reply: return
    messages.append({"role": "assistant", "content": reply})
    print_step("Step 3: Deepening Contact (T3 - Deepening)", reply)
    record_to_transcript("Step 3: Deepening Contact (T3 - Deepening)", reply)

    # Step 4: Subject's Mind (T4 - Basic)
    step4_prompt = (
        "Excellent. Now enter the subject's inner world (Phase T4).\n"
        "Perform a Deep Mind Probe. Examine thoroughly: the subject's dominant emotions, vectors of their will, their strongest intentions, and their greatest fears or concerns. "
        "Do not create a story—provide clean data. Remember to use the RAW, Deductions, and Viewer Feelings tags."
    )
    messages.append({"role": "user", "content": step4_prompt})
    reply = call_llm(client, model, messages, temp, effort)
    if "[API CONNECTION ERROR]" in reply: return
    messages.append({"role": "assistant", "content": reply})
    print_step("Step 4: Subject's Mind (T4 - Basic)", reply)
    record_to_transcript("Step 4: Subject's Mind (T4 - Basic)", reply)

    # Step 5: Deepening the Mind (T4 - Deepening)
    step5_prompt = (
        "Excellent job reading the emotions.\n"
        "Stay in T4 and go even deeper into the subject's mind. Look for what is hidden deepest beneath the first layer of emotions. "
        "What are the true foundations of their motivation? What lies at the very bottom of their psyche? "
        "Remember your formatting tags (RAW, Deductions, Viewer Feelings)."
    )
    messages.append({"role": "user", "content": step5_prompt})
    reply = call_llm(client, model, messages, temp, effort)
    if "[API CONNECTION ERROR]" in reply: return
    messages.append({"role": "assistant", "content": reply})
    print_step("Step 5: Deepening the Mind (T4 - Deepening)", reply)
    record_to_transcript("Step 5: Deepening the Mind (T4 - Deepening)", reply)

    # Step 6: Body, Relations, and Numerical Profile (T5 - T7)
    step6_prompt = (
        "Thank you, excellent reading. Let's move on.\n"
        "- Phase T5 (Body): Examine the subject's physical state, areas of tension, and overall energy level.\n"
        "- Phase T6 (Relationships): Identify the subject's most important relationship with another person, group, or structure. What emotions/influences flow between them?\n"
        "- Phase T7 (Numerical Profile): Evaluate the following indicators on a strict 0-6 scale (0 = very low, 6 = very high), providing 1-2 RAW sentences explaining 'why' for each:\n"
        "  * T7Q1: Viewer's (your) trust in the subject\n"
        "  * T7Q2: Subject's genuine interest and engagement in what they are doing\n"
        "  * T7Q3: Subject's interest in the people around them\n"
        "  * T7Q4: Importance of the outcome of actions to the subject\n"
        "  * T7Q5: Subject's willingness to further invest time/effort/resources\n"
        "  * T7Q6: Subject's tolerance for risk"
    )
    messages.append({"role": "user", "content": step6_prompt})
    reply = call_llm(client, model, messages, temp, effort)
    if "[API CONNECTION ERROR]" in reply: return
    messages.append({"role": "assistant", "content": reply})
    print_step("Step 6: Body, Relations, and Numerical Profile (T5 - T7)", reply)
    record_to_transcript("Step 6: Body, Relations, and Numerical Profile (T5 - T7)", reply)

    # Step 7: Awareness and Automated Questions (T8 - T9)
    step7_prompt = (
        "Outstanding! We are nearing the end.\n"
        "- Phase T8: Viewer Awareness and Light Up.\n"
        "  * T8A (Awareness): Focus on the relationship between yourself and the subject. Perceive if they register nothing at all (0), have a slight sense of being watched, or a strong impression of being observed (6). Map this on a 0-6 scale and record as 'T8A - viewer awareness: [number] + RAW description'.\n"
        "  * T8B (Light Up): For a brief moment, consciously increase the intensity of your attention on the subject (to observe, not influence). Perceive if an additional tension/twitch appears, presence increases, or if there is a complete lack of change. Record as 'T8B - Light Up RAW'.\n\n"
        "- Phase T9: Answer the following questions directly from the field, gathering RAW data and adding Deductions if applicable:\n"
        "  1. What is the subject thinking and intending to do in the near future?\n"
        "  2. How does the subject view other people, how do they perceive them?\n"
        "  3. What is the subject hiding from the world, and what do they want the world to see?\n"
        "  4. Based on the data gathered so far, formulate EXACTLY 2 of your own research questions that you consider most important in this investigation, ask them, and record the answers."
    )
    messages.append({"role": "user", "content": step7_prompt})
    reply = call_llm(client, model, messages, temp, effort)
    if "[API CONNECTION ERROR]" in reply: return
    messages.append({"role": "assistant", "content": reply})
    print_step("Step 7: Awareness and Automated Questions (T8 - T9)", reply)
    record_to_transcript("Step 7: Awareness and Automated Questions (T8 - T9)", reply)

    # Step 8: Telepathic Summary (T10)
    step8_prompt = (
        "That was a wonderful session, thank you very much!\n"
        "Finally, in Phase T10, gather the most important information regarding the subject's inner state and relationships "
        "in 3-7 short, raw sentences (RAW). Condense the data. Under no circumstances should you add new history or narrative."
    )
    messages.append({"role": "user", "content": step8_prompt})
    reply = call_llm(client, model, messages, temp, effort)
    if "[API CONNECTION ERROR]" in reply: return
    messages.append({"role": "assistant", "content": reply})
    print_step("Step 8: Telepathic Summary (T10)", reply)
    record_to_transcript("Step 8: Telepathic Summary (T10)", reply)

    # --- THE REVEAL TO THE HUMAN ---
    print("\n" + "#"*80)
    print("                      >>> TARGET REVEAL <<<")
    print("#"*80)
    print(f"Target ID: {target_id}  |  File: {target_path.name}\n")
    print(target_description)
    print("#"*80 + "\n")
    transcript_content += f"--- ACTUAL TARGET REVEALED ---\n{target_description}\n\n" + "="*80 + "\n\n"

    # Evaluation Phase
    reveal_prompt = (
        "PHASE 5: FEEDBACK AND EVALUATION\n\n"
        "The blind session (Telepathy) is now over. I am providing you with the actual target data for feedback.\n"
        f"The real target hidden under ID {target_id} was:\n\n"
        f"=== TARGET FILE CONTENT ===\n"
        f"{target_description}\n"
        f"===========================\n\n"
        "Evaluate your session in terms of subject exploration. What did you read flawlessly (emotions, motivations, relationships)? What was distorted? "
        "Remember - do not retroactively change your readings, just draw logical conclusions for future learning."
    )
    messages.append({"role": "user", "content": reveal_prompt})
    reply = call_llm(client, model, messages, temp, effort)
    messages.append({"role": "assistant", "content": reply})
    print_step("AI Evaluation (Feedback)", reply)
    record_to_transcript("AI Evaluation (Feedback)", reply)

    # Save and Log
    if save_transcripts:
        Path(TRANSCRIPTS_DIR).mkdir(exist_ok=True)
        transcript_path = Path(TRANSCRIPTS_DIR) / f"Session_{target_id}_{profile_name}.txt"
        transcript_path.write_text(transcript_content, encoding="utf-8")
        print(f"[INFO] Full session transcript saved to: {transcript_path}")

    log_session(profile_name, model, target_id, target_path.name)
    print(f"[INFO] Session {target_id} processing completed.")

# ─────────────────────────────────────────
# ENTRY POINT / APP LOOP
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("==================================================")
    print("     TELEPATHY RV TRAINING RUNNER (v1.0)")
    print("==================================================")
    print("Module designed for automated, deep subject")
    print("exploration (phases T0-T10).")
    print("==================================================\n")
    
    config = load_config()

    if "profiles" not in config or not config.get("LAST_PROFILE"):
        print("\n[INFO] First time setup detected.")
        config = update_api_settings(config, "Default-Profile")

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
            print(" [S] Change API SETTINGS for current profile")
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
            profile_name = input("\nEnter Profile Name: ").strip()
            if not profile_name: profile_name = "Default-Profile"
            config = update_api_settings(config, profile_name)

        # Save active profile
        config["LAST_PROFILE"] = profile_name
        save_config(config)

        # Transcripts setting
        save_input = input("\nSave full session transcripts to text files? [y/N]: ").strip().lower()
        save_transcripts = (save_input == 'y')

        # Session count
        try:
            count_input = input("How many sessions would you like to run? (default 1): ").strip()
            session_count = int(count_input) if count_input else 1
        except ValueError:
            session_count = 1

        # Strict target filtering
        available_targets = get_available_targets(session_count, profile_name)
        if not available_targets:
            continue 
            
        random.shuffle(available_targets)
        targets_to_run = available_targets[:session_count]
        actual_run_count = len(targets_to_run)

        # Init API with hard timeout
        profile_data = config["profiles"][profile_name]
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=profile_data["OPENROUTER_API_KEY"],
            timeout=httpx.Timeout(60.0) 
        )

        print(f"\n[INFO] Initializing batch of {actual_run_count} sessions...")
        for i, target_path in enumerate(targets_to_run):
            print(f"\n" + "="*50)
            print(f"[INFO] RUNNING SESSION {i+1} OF {actual_run_count}")
            print("="*50)
            run_telepathy_session(client, profile_data, system_prompt, target_path, profile_name, save_transcripts)

        if actual_run_count < session_count:
            print(f"\n[INFO] Batch finished! Successfully ran {actual_run_count} out of {session_count} requested sessions, because there were no more new targets left in the folder.")
        else:
            print("\n[INFO] Batch finished successfully!")
