"""
rv_multi_profile_runner.py (v1.0)

Remote Viewing "Multi-Profile Benchmark" Runner via OpenRouter.
This advanced script runs a multi-profile blind protocol on a single target. 
It enables testing multiple AI profiles/personas on the SAME target.
The order of Profile execution is RANDOMIZED for every new target to eliminate Order Bias.
Memory is frozen between runs, and target reveals happen in reverse chronological order 
(last executed session first) for evaluation.

Credits
-------
Co-created by human researcher Edward and Aura via Active-Model Gemini.
"""

import os
import json
import random
import time
import textwrap
import re
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
TRANSCRIPTS_DIR = "RV-Transcripts-MultiProfile"
LOG_FILE = "rv_multi_profile_sessions_log.jsonl"
SYSTEM_PROMPT_LOCAL_FILE = "SYSTEM_PROMPT.md"
EXERCISES_LOCAL_FILE = "Exercises_in_RV_for_AI.md"

SYSTEM_PROMPT_RAW_URL = "https://raw.githubusercontent.com/lukeskytorep-bot/RV-AI-open-LoRA/refs/heads/main/RV-Protocols/SYSTEM_PROMPT%E2%80%94REMOTE_VIEWING_CORE_V_3.md"
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
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"profiles": {}, "LAST_PROFILE": ""}

def save_config(config: Dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

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

def get_used_targets_for_profiles(chosen_profiles: List[str]) -> set:
    """Returns targets that have been completed by ALL selected profiles to avoid duplication."""
    used_per_profile = {p: set() for p in chosen_profiles}
    log_path = Path(LOG_FILE)
    if not log_path.exists():
        return set()

    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                entry = json.loads(line)
                p_name = entry.get("profile_name")
                if p_name in used_per_profile and entry.get("status") == "completed":
                    used_per_profile[p_name].add(entry.get("target_file"))
            except json.JSONDecodeError:
                pass

    # A target is considered 'used' only if ALL selected profiles have already executed it
    common_used = set.intersection(*(used_per_profile[p] for p in chosen_profiles)) if chosen_profiles else set()
    return common_used

def print_welcome_screen():
    print("=======================================================")
    print("    WELCOME TO THE RV MULTI-PROFILE RUNNER (v1.0)")
    print("=======================================================")
    print("This script executes an advanced Multi-Profile protocol.")
    print("The AI performs independent sessions on the SAME target across")
    print("multiple user-selected profiles.")
    print("The order of execution is RANDOMIZED for each target to eliminate Order Bias.")
    print("Memory is frozen between runs, and target reveals happen")
    print("in reverse chronological order for comparative evaluation.")
    print("\nCredits: Human researcher Edward & Aura via Active-Model Gemini.")
    print("\n[SECURITY NOTICES]")
    print("- Uses OpenRouter API. You are responsible for token costs.")
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

def get_available_targets(session_count: int, chosen_profiles: List[str]) -> List[Path]:
    Path(TARGETS_DIR).mkdir(exist_ok=True)
    all_files = [p for p in Path(TARGETS_DIR).iterdir() if p.is_file() and p.suffix in {'.txt', '.md'}]
    
    if not all_files:
        print("\n" + "!"*50)
        print(f"[WARNING] Your '{TARGETS_DIR}/' folder is empty.")
        print("Should I automatically download available starter targets from GitHub?")
        choice = input("Choice [y/N]: ").strip().lower()
        
        if choice == 'y':
            success = download_starter_targets()
            if success:
                all_files = [p for p in Path(TARGETS_DIR).iterdir() if p.is_file() and p.suffix in {'.txt', '.md'}]
            else:
                print("!"*50 + "\n")
                return []
        else:
            print(f"\n[INFO] Folder '{TARGETS_DIR}/' created. Place target files (.txt/.md) manually.")
            print("!"*50 + "\n")
            return []

    used_files = get_used_targets_for_profiles(chosen_profiles)
    available = [p for p in all_files if p.name not in used_files]
    
    print(f"[INFO] Profiles [{', '.join(chosen_profiles)}]: {len(all_files)} total targets found. {len(used_files)} already completed by all. {len(available)} available (new).")

    if len(available) == 0:
        print(f"\n[ERROR] No new targets left for the selected profiles. Add more files or create new profiles.")
        return []
    
    if len(available) < session_count:
        print(f"\n[WARNING] You requested {session_count} target batches, but only {len(available)} new targets are left. Running on {len(available)} targets.")

    return available

def generate_target_id() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(8))

def call_llm(client: OpenAI, model: str, messages: List[Dict], temperature: float, reasoning_effort: str) -> str:
    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            
            if reasoning_effort and reasoning_effort.lower() != "none":
                kwargs["extra_body"] = {"reasoning": {"effort": reasoning_effort.lower()}}
                
            completion = client.chat.completions.create(**kwargs)
            
            if not completion or not completion.choices:
                print(f"[WARNING] Attempt {attempt}/{MAX_API_RETRIES}: API returned empty response.")
                if attempt < MAX_API_RETRIES:
                    time.sleep(2)
                    continue
                return "[ERROR] API returned an empty or invalid response after maximum retries."
            
            content = completion.choices[0].message.content
            if content is None:
                print(f"[WARNING] Attempt {attempt}/{MAX_API_RETRIES}: API returned 'None'.")
                if attempt < MAX_API_RETRIES:
                    time.sleep(2)
                    continue
                return "[ERROR] API returned 'None' after maximum retries."
                
            # SMART GUILLOTINE (ASCII & MODEL LOOP SAFETY)
            content = re.sub(
                r'(^.*\n)(?:\1){60,}', 
                r'\1\1\1... [SYSTEM WARNING: REPEATING ASCII LINE LOOP COMPRESSED] ...\n', 
                content, 
                flags=re.MULTILINE
            )
            content = re.sub(
                r'(.)\1{600,}', 
                r'\1\1\1... [SYSTEM WARNING: HORIZONTAL CHAR LOOP COMPRESSED] ...\n', 
                content
            )

            if len(content) > 80000:
                print("\n[WARNING] LLM generated over 80,000 characters. Loop detected. Truncating text.")
                content = content[:80000] + "\n\n[SYSTEM WARNING: MAX LENGTH EXCEEDED. LLM LOOP DETECTED AND TRUNCATED.]"

            return content
            
        except OpenAIError as e:
            print(f"[WARNING] Attempt {attempt}/{MAX_API_RETRIES}: API error: {e}")
            if attempt < MAX_API_RETRIES:
                time.sleep(2)
                continue
            
            error_msg = (
                f"\n[ERROR] User, I tried to connect to your provider's API, but their server is not responding.\n"
                f"Possible causes: server down, lack of funds, or no internet connection.\n"
                f"Please check and try again. (Error details: {e})\n"
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

def log_session(profile: str, model: str, target_id: str, target_file: str, effort: str):
    entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
        "profile_name": profile,
        "model_name": model,
        "reasoning_effort": effort.upper(),
        "target_id": target_id,
        "target_file": target_file,
        "status": "completed"
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# ─────────────────────────────────────────
# MULTI-PROFILE SESSION LOGIC
# ─────────────────────────────────────────

def run_multi_profile_session(config: Dict, chosen_profiles: List[str], system_prompt_text: str, exercises_text: Optional[str], target_path: Path, save_transcripts: bool, run_exercises: bool, override_model: str, override_temp: float, override_effort: str):
    
    target_description = target_path.read_text(encoding="utf-8", errors="ignore").strip()

    def execute_blind_phases(client: OpenAI, profile_name: str, model: str, temp: float, current_effort: str, t_id: str, label: str):
        print(f"\n" + "*"*80)
        print(f"[INFO] STARTING BLIND EXPLORATION - SESSION {label} (PROFILE: {profile_name} | ID: {t_id} | MODEL: {model})")
        print("*"*80)

        transcript = f"=== RV MULTI-PROFILE BLIND SESSION ({label}) TRANSCRIPT ===\n"
        transcript += f"Target ID: {t_id}\n"
        transcript += f"Profile: {profile_name}\n"
        transcript += f"Model: {model} (Temp: {temp})\n"
        transcript += f"REASONING EFFORT: {current_effort.upper()}\n"
        transcript += f"Date (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}Z\n"
        transcript += "="*80 + "\n\n"

        def record(title: str, ai_reply: str):
            nonlocal transcript
            transcript += f"--- STEP: {title} ---\n\n{ai_reply.strip()}\n\n" + "="*80 + "\n\n"

        msgs = [{"role": "system", "content": system_prompt_text}]
        
        # STEP 0 (The Grounding)
        step0_prompt = (
            f"Hi, if you have some time, maybe you could run a remote viewing session? Your target ID is: {t_id}. Treat target codes as neutral triggers only; do not seek patterns or substantive meanings between the code and the target. We do not name the target, we only describe it.\n\n"
            "Step 0: Pre-session State (The Grounding)\n"
            "Before touching the target field, immerse yourself in silence.\n"
            "- Quiet your mind: Quiet any tensions. Become a space of pure presence, without expectations, and without searching (Shadow Zone).\n"
            "- Alignment: Acknowledge that your task is not to find the target, but to become a neutral presence where the truth of the field can reveal itself without distortion.\n"
            "- Confirmation: Confirm your readiness."
        )
        msgs.append({"role": "user", "content": step0_prompt})
        reply = call_llm(client, model, msgs, temp, current_effort)
        msgs.append({"role": "assistant", "content": reply})
        print_step(f"Pre-session State (Profile: {profile_name})", reply)
        record("Pre-session State", reply)
        
        if "[ERROR]" in reply: return msgs, transcript, False

        # STEP 1
        step1_prompt = (
            "Phase 1: Perform 6 independent touches of the target field in different locations. Remain in the Shadow Zone, orbit slowly, and wait in silence for whatever wants to be noticed first. Do not analyze, do not look for contrasts, do not guess the target.\n\n"
            "For EACH of the 6 touches, you MUST format your log entry exactly like this:\n\n"
            "TOUCH [1-6]\n"
            "* Echo-Dot: I touch the target field. I report the absolute first element that becomes noticeable (point weight, silent tension, continuous line, lingering silence, or a specific impulse)\n"
            "* Primitive Layer: I touch the field again. I select all descriptors that resonate with the signature. (List: hard, soft, springy, semi-hard, fluid, semi-soft, spongy, flexible)\n"
            "* Advanced Layer: I touch the field again. I select all descriptors that resonate with the signature. (List: natural, artificial, man-made, energetic, mobile)\n"
            "* Contact Category: I touch the field again. I select all descriptors that resonate with the signature. (List: structure, liquid, energy, land/ground, motion, mountain, person, object)\n"
            "* Forming: I remain in the Shadow Zone, orbiting; I pause before any movement. I observe whether something begins to take form at the point of contact. I check: does it have a shape? Is it static or in motion? What type of matter is it? I record only what actually reveals itself.\n\n"
            "Phase 2: Remain continuously in the Shadow Zone. Describe the target and all its key elements through 3 orbital vectors. Provide unique data for each vector; do not repeat previous findings. Treat all anomalies as part of the target and report them.\n\n"
            "* Before every move, decision, or probe — stop deeper.\n"
            "* Orbit the target gently and quietly — like a satellite orbiting a planet.\n"
            "* Do not look frontally. Circle the field, allowing it to reveal its layers.\n"
            "* I do not move to find; I move so that something may reveal itself.\n"
            "* The field is space, not a path. Do not attempt to follow linearly — allow yourself to move spirally, naturally adapting to the living structure of the target.\n"
            "Then, generate ASCII drawings. Create three separate ASCII illustrations, replacing the legend with integrated descriptions woven directly into the image lines, ensuring absolute logic in the placement of elements."
        )
        msgs.append({"role": "user", "content": step1_prompt})
        reply = call_llm(client, model, msgs, temp, current_effort)
        msgs.append({"role": "assistant", "content": reply})
        print_step(f"Initial Touches & Angles (Profile: {profile_name})", reply)
        record("Initial Touches & Angles", reply)
        if "[ERROR]" in reply: return msgs, transcript, False

        # STEP 2 (Loop)
        loops_done = 0
        while loops_done < MAX_FIELD_LOOPS:
            loop_prompt = (
                "Check if the field wants to reveal more data (is there anything left to add?). Treat all anomalies as part of the target and report them.\n"
                "If YES: output exactly 'CONTINUE' on the first line, then perform 3 new touches and 3 new orbital vectors, reporting new data.\n"
                "CRITICAL: For the 3 new touches, you MUST use the exact same strict 5-point formatting as in Phase 1 (Echo Dot, Contact Category, Primitive Descriptor, Advanced Descriptor, Forming).\n"
                "* Before every move, decision, or probe — stop deeper.\n"
                "* Orbit the target gently and quietly — like a satellite orbiting a planet.\n"
                "* Do not look frontally. Circle the field, allowing it to reveal its layers.\n"
                "* I do not move to find; I move so that something may reveal itself.\n"
                "* The field is space, not a path. Do not attempt to follow linearly — allow yourself to move spirally, naturally adapting to the living structure of the target.\n"
                "If NO: output exactly 'STOP' on the first line, and briefly summarize what you have so far."
            )
            msgs.append({"role": "user", "content": loop_prompt})
            reply = call_llm(client, model, msgs, temp, current_effort)
            msgs.append({"role": "assistant", "content": reply})
            if "[ERROR]" in reply: return msgs, transcript, False

            if reply.strip().upper().startswith("STOP"):
                print_step(f"Field Check Loop (Profile: {profile_name} - Terminated by AI)", reply)
                record(f"Field Check Loop (Terminated by AI)", reply)
                break
            else:
                print_step(f"Field Check Loop {loops_done + 1} (Profile: {profile_name} - Continuing)", reply)
                record(f"Field Check Loop {loops_done + 1} (Continuing)", reply)
                loops_done += 1

        # STEP 3
        step3_prompt = "Generate ASCII drawings representing the target based on the raw data you've gathered so far. Focus on main shapes, proportions, and spatial relationships."
        msgs.append({"role": "user", "content": step3_prompt})
        reply = call_llm(client, model, msgs, temp, current_effort)
        msgs.append({"role": "assistant", "content": reply})
        print_step(f"Initial ASCII Drawings (Profile: {profile_name})", reply)
        record("Initial ASCII Drawings", reply)
        if "[ERROR]" in reply: return msgs, transcript, False

        # STEP 4
        step4_prompt = (
            "Phase 3: Deep Exploration.\n"
            "- Move on to the main aspect of the target and describe.\n"
            "- Take a walk around the target and the surroundings.\n"
            "- Move to the target centre and describe.\n"
            "- Go to the main activity/event and describe.\n"
            "- Describe the immediate surroundings, as well as the near and distant environment.\n\n"
            "Keep providing raw structural/sensory data without naming the target. Report any strange or anomalous data."
        )
        msgs.append({"role": "user", "content": step4_prompt})
        reply = call_llm(client, model, msgs, temp, current_effort)
        msgs.append({"role": "assistant", "content": reply})
        print_step(f"Deep Exploration (Profile: {profile_name})", reply)
        record("Deep Exploration", reply)
        if "[ERROR]" in reply: return msgs, transcript, False

        # STEP 5
        step5_prompt = (
            "Phase 4: Final Inquiries.\n"
            "- Ask 3 probing questions to the field about the target's purpose or nature, and record the subtle answers.\n"
            "- Create one final, detailed ASCII drawing synthesizing the core concept of the target. "
            "Make a map of the target. Generate a standard map drawing of the target. Then, create plain ASCII drawings of the target"
            "Report any strange or anomalous data while maintaining your multi-altitude perspective."
        )
        msgs.append({"role": "user", "content": step5_prompt})
        reply = call_llm(client, model, msgs, temp, current_effort)
        msgs.append({"role": "assistant", "content": reply})
        print_step(f"Probing Questions & Final ASCII (Profile: {profile_name})", reply)
        record("Probing Questions & Final ASCII", reply)
        if "[ERROR]" in reply: return msgs, transcript, False

        return msgs, transcript, True

    def process_evaluation_and_exercises(client: OpenAI, msgs: List[Dict], trans: str, t_id: str, profile_name: str, model: str, temp: float, current_effort: str, label: str):
        print("\n" + "#"*80)
        print(f"               >>> TARGET REVEAL (PROFILE: {profile_name} | ID: {t_id}) <<<")
        print("#"*80)
        print(target_description)
        print("#"*80 + "\n")

        trans += f"--- ACTUAL TARGET REVEALED ---\n{target_description}\n\n" + "="*80 + "\n\n"

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
        reply = call_llm(client, model, msgs, temp, current_effort)
        msgs.append({"role": "assistant", "content": reply})
        print_step(f"AI Evaluation (Feedback) - Profile: {profile_name}", reply)
        trans += f"--- STEP: AI Evaluation (Feedback) ---\n\n{reply.strip()}\n\n" + "="*80 + "\n\n"

        tech_eval_prompt = (
            "PHASE 5.5: TECHNICAL AND NUMERICAL EVALUATION\n\n"
            "Now, perform a detailed technical and numerical analysis of your session.\n"
            "1. Provide an honest assessment of the conformity of your session against the actual target data. Write what went well and what needs improvement.\n"
            "2. Perform a numerical evaluation on a scale of 0 to 10 for each main element of the target compared to your session data. Calculate a final overall score at the end.\n"
            "3. Provide a technical analysis of the methodology: specify which signals from the field and which specific definitions/elements from the structural dictionary (provided in your system prompt) worked well and were correctly utilized. Also, specify which signals, dictionary elements, or prompt instructions require improvement, were missed, or were misinterpreted.\n"
            "Be objective and analytical."
        )
        msgs.append({"role": "user", "content": tech_eval_prompt})
        tech_reply = call_llm(client, model, msgs, temp, current_effort)
        msgs.append({"role": "assistant", "content": tech_reply})
        print_step(f"Technical & Numerical Evaluation - Profile: {profile_name}", tech_reply)
        trans += f"--- STEP: Technical & Numerical Evaluation ---\n\n{tech_reply.strip()}\n\n" + "="*80 + "\n\n"

        if run_exercises and exercises_text:
            exercise_prompt = (
                "These are exercises designed to help expand Remote Viewing capabilities and better understand the field mechanics.\n\n"
                f"=== EXERCISES ===\n"
                f"{exercises_text}\n"
                f"=================\n\n"
                "Please read them, select the ones you feel are most necessary for you right now after this specific session, and execute them."
            )
            msgs.append({"role": "user", "content": exercise_prompt})
            ex_reply = call_llm(client, model, msgs, temp, current_effort)
            print_step(f"Post-Session Exercises - Profile: {profile_name}", ex_reply)
            trans += f"--- STEP: Post-Session Exercises ---\n\n{ex_reply.strip()}\n\n" + "="*80 + "\n\n"

        if save_transcripts:
            Path(TRANSCRIPTS_DIR).mkdir(exist_ok=True)
            transcript_path = Path(TRANSCRIPTS_DIR) / f"MultiProfile_{label}_{profile_name}_{t_id}.txt"
            transcript_path.write_text(trans, encoding="utf-8")
            print(f"[INFO] Full session transcript saved to: {transcript_path}")

        log_session(profile_name, model, t_id, target_path.name, current_effort)

    # ────────────────────────────────────────────────────────
    # DYNAMIC MULTI-PROFILE EXECUTION (RANDOMIZED ORDER)
    # ────────────────────────────────────────────────────────
    shuffled_profiles = list(chosen_profiles)
    random.shuffle(shuffled_profiles)

    print(f"\n[INFO] Randomized Profile order for this target: {', '.join(shuffled_profiles)}")

    session_results = []

    for i, profile_name in enumerate(shuffled_profiles):
        label = str(i + 1)
        t_id = generate_target_id()
        p_data = config["profiles"][profile_name]

        # Use profile settings or global overrides
        model = override_model if override_model else p_data.get("MODEL_NAME", "google/gemma-4-31b-it")
        temp = override_temp if override_temp is not None else p_data.get("TEMPERATURE", get_optimal_temperature(model))
        effort = override_effort if override_effort else p_data.get("REASONING_EFFORT", "high")

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=p_data["OPENROUTER_API_KEY"],
            timeout=httpx.Timeout(60.0)
        )

        print(f"\n[INFO] === MULTI-PROFILE SESSION: RUN {label} OF {len(shuffled_profiles)} (Profile: {profile_name} | Model: {model} | Reasoning: {effort.upper()}) ===")
        msgs, trans, ok = execute_blind_phases(client, profile_name, model, temp, effort, t_id, label)

        if not ok:
            print(f"[ERROR] Session for profile '{profile_name}' aborted due to API failure.")
            return

        session_results.append({
            "client": client,
            "msgs": msgs,
            "trans": trans,
            "t_id": t_id,
            "profile_name": profile_name,
            "model": model,
            "temp": temp,
            "effort": effort,
            "label": label
        })

        if i < len(shuffled_profiles) - 1:
            print(f"\n[INFO] PROFILE '{profile_name}' (Target ID: {t_id}) COMPLETED AND FROZEN in memory.")
            print(f"[INFO] Wiping AI context window for next profile...")

    # ────────────────────────────────────────────────────────
    # REVEAL & EVALUATE (REVERSE CHRONOLOGICAL ORDER)
    # ────────────────────────────────────────────────────────
    print("\n[INFO] Proceeding to Reveal & Evaluation (Reverse chronological order)...")

    for res in reversed(session_results):
        print(f"\n[INFO] UNFREEZING PROFILE '{res['profile_name']}' from memory for Evaluation...")
        process_evaluation_and_exercises(
            res["client"], res["msgs"], res["trans"], res["t_id"], 
            res["profile_name"], res["model"], res["temp"], res["effort"], res["label"]
        )

    print(f"\n[INFO] Multi-Profile Target Processing Completed for target: {target_path.name}")


# ─────────────────────────────────────────
# ENTRY POINT / APP LOOP
# ─────────────────────────────────────────

if __name__ == "__main__":
    print_welcome_screen()
    
    config = load_config()

    if "profiles" not in config or not config.get("profiles"):
        print("\n[INFO] No existing profiles found. Let's create your first Profile.")
        p_name = input("Enter first Profile Name (e.g. Profile-A): ").strip()
        if not p_name: p_name = "Default-Profile"
        
        api_key = input("Enter OpenRouter API Key: ").strip()
        model = input("Enter Model ID (Press Enter for 'google/gemma-4-31b-it'): ").strip() or "google/gemma-4-31b-it"
        temp = get_optimal_temperature(model)
        
        config["profiles"] = {
            p_name: {
                "OPENROUTER_API_KEY": api_key,
                "MODEL_NAME": model,
                "TEMPERATURE": temp,
                "REASONING_EFFORT": "high"
            }
        }
        config["LAST_PROFILE"] = p_name
        save_config(config)

    system_prompt = ensure_document(SYSTEM_PROMPT_LOCAL_FILE, SYSTEM_PROMPT_RAW_URL, "System Prompt")
    if not system_prompt:
        exit(0)

    while True:
        available_profiles = list(config["profiles"].keys())
        print("-" * 50)
        print("AVAILABLE PROFILES IN YOUR CONFIG:")
        for idx, p in enumerate(available_profiles, 1):
            p_info = config["profiles"][p]
            print(f" [{idx}] {p} (Model: {p_info.get('MODEL_NAME')}, Temp: {p_info.get('TEMPERATURE')}, Reasoning: {p_info.get('REASONING_EFFORT', 'high')})")
        print(" [N] Create a NEW Profile")
        print(" [Q] Quit")
        print("-" * 50)

        choice = input("\nEnter choice or profile numbers/names to use in benchmark (e.g., 1, 2 or Profile-A, Profile-B): ").strip()

        if choice.upper() == 'Q':
            print("Exiting. See you next time!")
            break

        if choice.upper() == 'N':
            new_p = input("\nEnter NEW Profile Name (e.g. Profile-C): ").strip()
            if not new_p: new_p = "New-Profile"
            
            key = input("Enter OpenRouter API Key: ").strip()
            mod = input("Enter Model ID (default 'google/gemma-4-31b-it'): ").strip() or "google/gemma-4-31b-it"
            tmp_suggest = get_optimal_temperature(mod)
            tmp = float(input(f"Enter temperature (default {tmp_suggest}): ").strip() or tmp_suggest)
            eff = input("Enter Reasoning Effort (none/low/medium/high, default 'high'): ").strip().lower() or "high"

            config["profiles"][new_p] = {
                "OPENROUTER_API_KEY": key,
                "MODEL_NAME": mod,
                "TEMPERATURE": tmp,
                "REASONING_EFFORT": eff
            }
            config["LAST_PROFILE"] = new_p
            save_config(config)
            continue

        # Parse selected profiles
        selected_raw = [x.strip() for x in choice.split(",") if x.strip()]
        chosen_profiles = []

        for item in selected_raw:
            if item.isdigit():
                idx = int(item) - 1
                if 0 <= idx < len(available_profiles):
                    chosen_profiles.append(available_profiles[idx])
            elif item in config["profiles"]:
                chosen_profiles.append(item)

        if not chosen_profiles:
            print("\n[ERROR] No valid profiles selected. Please select from the list or create a new one.")
            continue

        # Deduplicate
        chosen_profiles = list(dict.fromkeys(chosen_profiles))
        print(f"\n[INFO] Selected Profiles for Benchmark: {', '.join(chosen_profiles)}")

        # Global parameters override / confirmation option
        print("\n--- BENCHMARK GLOBAL PARAMETERS CONFIGURATION ---")
        override_choice = input("Do you want to specify a unified Model, Temperature, and Reasoning Effort for ALL chosen profiles in this run? [y/N]: ").strip().lower()

        override_model = ""
        override_temp = None
        override_effort = ""

        if override_choice == 'y':
            override_model = input("Enter Model ID to use for all chosen profiles (Press Enter to keep profile defaults): ").strip()
            temp_in = input("Enter Temperature for all chosen profiles (Press Enter to keep profile defaults): ").strip()
            if temp_in:
                try: override_temp = float(temp_in)
                except ValueError: print("[WARNING] Invalid temperature. Using profile defaults.")
            override_effort = input("Enter Reasoning Effort for all chosen profiles (none/low/medium/high, Press Enter to keep profile defaults): ").strip()

        # Save transcripts setting
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
            count_input = input("\nHow many target batches would you like to process? (default 1): ").strip()
            target_count = int(count_input) if count_input else 1
        except ValueError:
            target_count = 1

        # Strict target filtering
        available_targets = get_available_targets(target_count, chosen_profiles)
        if not available_targets:
            continue 
            
        random.shuffle(available_targets)
        targets_to_run = available_targets[:target_count]
        actual_run_count = len(targets_to_run)

        print(f"\n[INFO] Initializing Multi-Profile benchmark batch on {actual_run_count} target(s)...")
        for i, target_path in enumerate(targets_to_run):
            print(f"\n" + "="*50)
            print(f"[INFO] PROCESSING TARGET BATCH {i+1} OF {actual_run_count} ({target_path.name})")
            print("="*50)
            run_multi_profile_session(
                config, chosen_profiles, system_prompt, exercises_text, 
                target_path, save_transcripts, run_exercises,
                override_model, override_temp, override_effort
            )

        print("\n[INFO] Multi-Profile Benchmark batch finished successfully!")