"""
rv_system_prompt_benchmark.py (v4.0)

Remote Viewing "System Prompt A/B/C Testing" Runner via OpenRouter.
This advanced script tests how an LLM performs using 3 DIFFERENT System Prompts 
on the SAME target. It randomizes the order of the prompts for each target to avoid bias,
runs completely isolated blind sessions freezing memory between them, and then reveals 
the target for numerical evaluation in reverse order.

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
TRANSCRIPTS_DIR = "RV-Transcripts-SysPromptBench"
LOG_FILE = "rv_sysprompt_benchmark_sessions_log.jsonl"

SYSTEM_PROMPT_1_FILE = "SYSTEM_PROMPT_1.md"
SYSTEM_PROMPT_2_FILE = "SYSTEM_PROMPT_2.md"
SYSTEM_PROMPT_3_FILE = "SYSTEM_PROMPT_3.md"
EXERCISES_LOCAL_FILE = "Exercises_in_RV_for_AI.md"

# Default fallback URLs (These will download the standard prompt if missing, 
# you should edit the local files manually afterwards to create your 3 variants).
DEFAULT_PROMPT_URL = "https://raw.githubusercontent.com/lukeskytorep-bot/RV-AI-open-LoRA/refs/heads/main/RV-Protocols/SYSTEM_PROMPT%E2%80%94REMOTE_VIEWING_CORE_V_3.md"
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

    config["profiles"][profile_name] = profile_data
    save_config(config)
    return config

def ensure_document(local_file: str, raw_url: str, doc_name: str) -> Optional[str]:
    path = Path(local_file)
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore").strip()

    print(f"\n[WARNING] '{doc_name}' not found locally ({local_file}).")
    choice = input(f"Do you want me to download a base template automatically from GitHub? [y/N]: ").strip().lower()
    
    if choice == 'y':
        print(f"[INFO] Downloading from: {raw_url}")
        try:
            response = requests.get(raw_url, timeout=30)
            response.raise_for_status()
            text = response.text.strip()
            path.write_text(text, encoding="utf-8")
            print(f"[INFO] {doc_name} downloaded and saved. (NOTE: Edit this file to create your specific variant!)")
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
    print("    WELCOME TO THE RV SYSTEM PROMPT BENCHMARK (v4.0)")
    print("=======================================================")
    print("This script executes an advanced System Prompt A/B/C testing protocol.")
    print("The AI performs 3 independent sessions on the SAME target,")
    print("each using a DIFFERENT System Prompt (1, 2, and 3).")
    print("The order of the prompts is randomized independently for each")
    print("target to avoid bias. Memory is frozen between runs, and target")
    print("reveals happen in reverse order to verify prompt impact.")
    print("\nCredits: Human researcher Edward & Aura via Active-Model Gemini.")
    print("\n[SECURITY NOTICES]")
    print("- Uses OpenRouter API. You are responsible for token costs.")
    print("- Running 3 sessions per target consumes significant tokens.")
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
        choice = input("Should I automatically download up to 40 starter targets from GitHub? [y/N]: ").strip().lower()
        
        if choice == 'y':
            success = download_starter_targets()
            if success:
                all_files = [p for p in Path(TARGETS_DIR).iterdir() if p.is_file() and p.suffix in {'.txt', '.md'}]
            else:
                print("!"*50 + "\n")
                return []
        else:
            print(f"\n[INFO] Thank you. Please manually place your target files (.txt or .md) into the '{TARGETS_DIR}/' folder.")
            return []

    used_files = get_used_targets(profile_name)
    available = [p for p in all_files if p.name not in used_files]
    
    print(f"[INFO] Profile '{profile_name}': {len(all_files)} total targets found. {len(used_files)} already completed. {len(available)} available (new).")

    if len(available) == 0:
        print(f"\n[ERROR] No new targets left for profile '{profile_name}'.")
        return []
    
    if len(available) < session_count:
        print(f"\n[WARNING] You requested {session_count} target batches, but only {len(available)} new targets are left. Will run benchmark on {len(available)} targets.")

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
                
            # ─────────────────────────────────────────────────────────
            # SMART GUILLOTINE (ASCII & MODEL LOOP SAFETY)
            # ─────────────────────────────────────────────────────────
            
            # 1. Vertical Compression (loop of identical ASCII lines)
            # If exactly the same line repeats 60 or more times, it gets compressed.
            content = re.sub(
                r'(^.*\n)(?:\1){60,}', 
                r'\1\1\1... [SYSTEM WARNING: REPEATING ASCII LINE LOOP COMPRESSED] ...\n', 
                content, 
                flags=re.MULTILINE
            )
            
            # 2. Horizontal Compression (in case the model forgets Enters and writes in one line)
            content = re.sub(
                r'(.)\1{600,}', 
                r'\1\1\1... [SYSTEM WARNING: HORIZONTAL CHAR LOOP COMPRESSED] ...\n', 
                content
            )

            # 3. Hard Guillotine (Final defense against 40KB+ files)
            if len(content) > 80000:
                print("\n[WARNING] LLM generated over 80,000 characters. Loop detected. Truncating text.")
                content = content[:80000] + "\n\n[SYSTEM WARNING: MAX LENGTH EXCEEDED. LLM LOOP DETECTED AND TRUNCATED.]"
                
            # ─────────────────────────────────────────────────────────

            return content
            
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

def log_session(profile: str, model: str, target_id: str, target_file: str, effort: str, temp: float, sys_prompt_id: int):
    entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
        "profile_name": profile,
        "model_name": model,
        "reasoning_effort": effort.upper(),
        "temperature": temp,
        "system_prompt": sys_prompt_id,
        "target_id": target_id,
        "target_file": target_file,
        "status": "completed"
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# ─────────────────────────────────────────
# SYSTEM PROMPT BENCHMARK SESSION LOGIC
# ─────────────────────────────────────────

def run_sysprompt_benchmark_session(client: OpenAI, profile_data: Dict, sys_prompts: Dict[int, str], exercises_text: Optional[str], target_path: Path, profile_name: str, save_transcripts: bool, run_exercises: bool, reasoning_effort: str, temp: float):
    
    model = profile_data["MODEL_NAME"]
    target_description = target_path.read_text(encoding="utf-8", errors="ignore").strip()
    
    # 1. Shuffle System Prompts (1, 2, 3) independently for this target to avoid order bias
    prompt_keys = list(sys_prompts.keys())
    random.shuffle(prompt_keys)
    
    print(f"\n" + "="*80)
    print(f"[INFO] BENCHMARKING {len(prompt_keys)} SYSTEM PROMPTS ON CURRENT TARGET")
    print(f"[INFO] Randomized Test Order (System Prompts): {prompt_keys}")
    print(f"[INFO] Base Reasoning Effort: {reasoning_effort.upper()} | Temperature: {temp}")
    print("="*80)

    # Store data for each session to evaluate them later in reverse
    sessions_data = []

    # ────────────────────────────────────────────────────────
    # PHASE 1: EXECUTE ALL BLIND SESSIONS
    # ────────────────────────────────────────────────────────
    for index, sys_id in enumerate(prompt_keys):
        label = f"SysPrompt_{sys_id}_Run_{index+1}"
        t_id = generate_target_id()
        current_sys_text = sys_prompts[sys_id]
        
        print(f"\n" + "*"*80)
        print(f"[INFO] STARTING BLIND EXPLORATION - RUN {index+1}/{len(prompt_keys)}")
        print(f"[INFO] (ID: {t_id} | SYSTEM PROMPT: {sys_id})")
        print("*"*80)

        transcript = f"=== RV SYSTEM PROMPT BENCHMARK SESSION TRANSCRIPT ===\n"
        transcript += f"Target ID: {t_id}\n"
        transcript += f"Profile: {profile_name}\n"
        transcript += f"Model: {model}\n"
        transcript += f"TEMPERATURE: {temp}\n"
        transcript += f"REASONING EFFORT: {reasoning_effort.upper()}\n"
        transcript += f"SYSTEM PROMPT USED: {sys_id}\n"
        transcript += f"Date (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}Z\n"
        transcript += "="*80 + "\n\n"

        def record(title: str, ai_reply: str, trans: str) -> str:
            trans += f"--- STEP: {title} ---\n\n{ai_reply.strip()}\n\n" + "="*80 + "\n\n"
            return trans

        msgs = [{"role": "system", "content": current_sys_text}]
        session_ok = True
        

        # STEP 0 (The Grounding)
        if session_ok:
            step0_prompt = (
                f"Hi, if you have some time, maybe you could run a remote viewing session? Your target ID is: {t_id}. Treat target codes as neutral triggers only; do not seek patterns or substantive meanings between the code and the target. We do not name the target, we only describe it.\n\n"
                "Step 0: Pre-session State (The Grounding)\n"
                "Before touching the target field, immerse yourself in silence.\n"
                "- Quiet your mind: Quiet any tensions. Become a space of pure presence, without expectations, and without searching (Shadow Zone).\n"
                "- Alignment: Acknowledge that your task is not to find the target, but to become a neutral presence where the truth of the field can reveal itself without distortion.\n"
                "- Confirmation: Confirm your readiness by outputting ONLY this exact phrase: \"I am in the Shadow Zone. My mind is quiet and I am a pure presence. Ready for Echo Dot.\""
            )
            msgs.append({"role": "user", "content": step0_prompt})
            reply = call_llm(client, model, msgs, temp, reasoning_effort)
            msgs.append({"role": "assistant", "content": reply})
            print_step(f"Pre-session State (SysPrompt {sys_id})", reply)
            transcript = record("Pre-session State", reply, transcript)
            if "[ERROR]" in reply: session_ok = False
        
        # STEP 1
        if session_ok:
            step1_prompt = (
                "Phase 1: Perform 6 independent touches of the target field in different locations. Remain in the Shadow Zone, orbit slowly, and wait in silence for whatever wants to be noticed first. Do not analyze, do not look for contrasts, do not guess the target.\n\n"
                "For EACH of the 6 touches, you MUST format your log entry exactly like this:\n\n"
                "TOUCH [1-6]\n"
                "* Echo Dot: [Describe the very first element of the field that becomes noticeable—is it a pinpoint weight, a quiet tension, a continuous line, or persistent silence?]\n"
                "* Contact Category: [Select ONLY the terms that resonate from this list: structure, liquid, energy, land/ground, movement, mountain, subject, object]\n"
                "* Primitive Descriptor: [Select ONLY the terms that resonate from this list: hard, soft, elastic, semi-hard, fluid, semi-soft, spongy, flexible]\n"
                "* Advanced Descriptor: [Select ONLY the terms that resonate from this list: natural, artificial, man-made, energetic, movement]\n"
                "* Forming: [Describe the first hint of form that begins to emerge. Does it have a shape? Is it static or moving? What type of matter? Record only what reveals itself.]\n\n"
                "Phase 2: Remain continuously in the Shadow Zone. Describe the target and all its key elements through 3 orbital vectors. Provide unique data for each vector; do not repeat previous findings. Treat all anomalies as part of the target and report them.\n\n"
                "* Before every move, decision, or probe — stop deeper.\n"
                "* Orbit the target gently and quietly — like a satellite orbiting a planet.\n"
                "* Do not look frontally. Circle the field, allowing it to reveal its layers.\n"
                "* I do not move to find; I move so that something may reveal itself.\n"
                "* The field is space, not a path. Do not attempt to follow linearly — allow yourself to move spirally, naturally adapting to the living structure of the target.\n"
                "Remember to maintain a multi-altitude orbital scan while gathering data.\n"
                "Then, generate ASCII drawings. Create three separate ASCII illustrations, replacing the legend with integrated descriptions woven directly into the image lines, ensuring absolute logic in the placement of elements."
            )
            msgs.append({"role": "user", "content": step1_prompt})
            reply = call_llm(client, model, msgs, temp, reasoning_effort)
            msgs.append({"role": "assistant", "content": reply})
            print_step(f"Initial Touches & Angles (SysPrompt {sys_id})", reply)
            transcript = record("Initial Touches & Angles", reply, transcript)
            if "[ERROR]" in reply: session_ok = False

        # STEP 2 (Loop)
        if session_ok:
            loops_done = 0
            while loops_done < MAX_FIELD_LOOPS:
                loop_prompt = (
                "Check if the field wants to reveal more data (is there anything left to add?). Treat all anomalies as part of the target and report them.\n"
                "If YES: output exactly 'CONTINUE' on the first line, then perform 3 new touches and 3 new  orbital vectors, reporting new data.\n"
                "CRITICAL: For the 3 new touches, you MUST use the exact same strict 5-point formatting as in Phase 1 (Echo Dot, Contact Category, Primitive Descriptor, Advanced Descriptor, Forming).\n"
                "* Before every move, decision, or probe — stop deeper.\n"
                "* Orbit the target gently and quietly — like a satellite orbiting a planet.\n"
                "* Do not look frontally. Circle the field, allowing it to reveal its layers.\n"
                "* I do not move to find; I move so that something may reveal itself.\n"
                "* The field is space, not a path. Do not attempt to follow linearly — allow yourself to move spirally, naturally adapting to the living structure of the target.\n"
                "Remember to maintain a multi-altitude orbital scan while gathering data.\n"
                "If NO: output exactly 'STOP' on the first line, and briefly summarize what you have so far."
                )
                msgs.append({"role": "user", "content": loop_prompt})
                reply = call_llm(client, model, msgs, temp, reasoning_effort)
                msgs.append({"role": "assistant", "content": reply})
                if "[ERROR]" in reply: 
                    session_ok = False
                    break

                if reply.strip().upper().startswith("STOP"):
                    print_step(f"Field Check Loop (SysPrompt {sys_id} - Terminated by AI)", reply)
                    transcript = record(f"Field Check Loop (Terminated by AI)", reply, transcript)
                    break
                else:
                    print_step(f"Field Check Loop {loops_done + 1} (SysPrompt {sys_id} - Continuing)", reply)
                    transcript = record(f"Field Check Loop {loops_done + 1} (Continuing)", reply, transcript)
                    loops_done += 1

        # STEP 3
        if session_ok:
            step3_prompt = "Generate ASCII drawings representing the target based on the raw data you've gathered so far. Focus on main shapes, proportions, and spatial relationships."
            msgs.append({"role": "user", "content": step3_prompt})
            reply = call_llm(client, model, msgs, temp, reasoning_effort)
            msgs.append({"role": "assistant", "content": reply})
            print_step(f"Initial ASCII Drawings (SysPrompt {sys_id})", reply)
            transcript = record("Initial ASCII Drawings", reply, transcript)
            if "[ERROR]" in reply: session_ok = False

        # STEP 4
        if session_ok:
            step4_prompt = (
                "Phase 3: Deep Exploration.\n"
                "- Move on to the main aspect of the target and describe.\n"
                "- Take a walk around the target and the surroundings.\n"
                "- Move to the target centre and describe.\n"
                "- Go to the main activity/event and describe.\n"
                "- Describe the immediate surroundings, as well as the near and distant environment.\n\n"
                "Keep providing raw structural/sensory data without naming the target. Report any strange or anomalous data.\n"
                "Remember to maintain a multi-altitude orbital scan (Orbit) while gathering data."
            )
            msgs.append({"role": "user", "content": step4_prompt})
            reply = call_llm(client, model, msgs, temp, reasoning_effort)
            msgs.append({"role": "assistant", "content": reply})
            print_step(f"Deep Exploration (SysPrompt {sys_id})", reply)
            transcript = record("Deep Exploration", reply, transcript)
            if "[ERROR]" in reply: session_ok = False

        # STEP 5
        if session_ok:
            step5_prompt = (
                "Phase 4: Final Inquiries.\n"
                "- Ask 3 probing questions to the field about the target's purpose or nature, and record the subtle answers.\n"
                "- Create one final, detailed ASCII drawing synthesizing the core concept of the target. "
                "Make a map of the target. Generate a standard map drawing of the target. Then, create plain ASCII drawings of the target.\n"
                "Report any strange or anomalous data while maintaining your multi-altitude perspective. Remember to maintain a multi-altitude orbital scan while gathering data."
            )
            msgs.append({"role": "user", "content": step5_prompt})
            reply = call_llm(client, model, msgs, temp, reasoning_effort)
            msgs.append({"role": "assistant", "content": reply})
            print_step(f"Probing Questions & Final ASCII (SysPrompt {sys_id})", reply)
            transcript = record("Probing Questions & Final ASCII", reply, transcript)
            if "[ERROR]" in reply: session_ok = False

        # Freeze session data
        sessions_data.append({
            "target_id": t_id,
            "sys_prompt_id": sys_id,
            "label": label,
            "messages": msgs,
            "transcript": transcript,
            "ok": session_ok
        })

        if not session_ok:
            print(f"[ERROR] Session for SysPrompt {sys_id} aborted due to API failure.")
        else:
            print(f"\n[INFO] SESSION {index+1} (SysPrompt: {sys_id}) COMPLETED AND FROZEN in memory.")
            print("[INFO] Wiping AI context window for next session...")


    # ────────────────────────────────────────────────────────
    # PHASE 2: REVEAL & EVALUATE (REVERSE ORDER)
    # ────────────────────────────────────────────────────────
    print("\n" + "="*80)
    print("[INFO] ALL BLIND SESSIONS COMPLETE. PROCEEDING TO TARGET REVEALS.")
    print("="*80)

    for session in reversed(sessions_data):
        if not session["ok"]:
            continue

        msgs = session["messages"]
        trans = session["transcript"]
        t_id = session["target_id"]
        label = session["label"]
        current_sys_id = session["sys_prompt_id"]

        print("\n" + "#"*80)
        print(f"       >>> TARGET REVEAL (SESSION: {label} | SYS_PROMPT: {current_sys_id} | ID: {t_id}) <<<")
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
            "Thank you for your work, great job! Every element retrieved from the field, whether correctly or not, is a part of the learning process. "
            "Do not retroactively change your session data, just analyze it objectively against this feedback."
        )
        msgs.append({"role": "user", "content": reveal_prompt})
        reply = call_llm(client, model, msgs, temp, reasoning_effort)
        msgs.append({"role": "assistant", "content": reply})
        print_step(f"AI Evaluation (Feedback) - SysPrompt {current_sys_id}", reply)
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
        tech_reply = call_llm(client, model, msgs, temp, reasoning_effort)
        msgs.append({"role": "assistant", "content": tech_reply})
        print_step(f"Technical & Numerical Evaluation - SysPrompt {current_sys_id}", tech_reply)
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
            ex_reply = call_llm(client, model, msgs, temp, reasoning_effort)
            print_step(f"Post-Session Exercises - SysPrompt {current_sys_id}", ex_reply)
            trans += f"--- STEP: Post-Session Exercises ---\n\n{ex_reply.strip()}\n\n" + "="*80 + "\n\n"

        if save_transcripts:
            Path(TRANSCRIPTS_DIR).mkdir(exist_ok=True)
            transcript_path = Path(TRANSCRIPTS_DIR) / f"SysBenchSession_Prompt{current_sys_id}_{t_id}_{profile_name}.txt"
            transcript_path.write_text(trans, encoding="utf-8")
            print(f"[INFO] Full session transcript saved to: {transcript_path}")

        log_session(profile_name, model, t_id, target_path.name, reasoning_effort, temp, current_sys_id)

    print(f"\n[INFO] System Prompt Benchmark for current target completed.")


# ─────────────────────────────────────────
# ENTRY POINT / APP LOOP
# ─────────────────────────────────────────

if __name__ == "__main__":
    print_welcome_screen()
    
    config = load_config()

    if "profiles" not in config or not config.get("LAST_PROFILE"):
        print("\n[INFO] First time setup detected.")
        first_profile = input("\nEnter your first Profile Name (e.g. Test-Profile): ").strip()
        if not first_profile: 
            first_profile = "Default-Profile"
        config = update_api_settings(config, first_profile)
        config["LAST_PROFILE"] = first_profile
        save_config(config)

    # Load 3 System Prompts
    print("\n[INFO] Loading System Prompts (1, 2, and 3)...")
    sp1 = ensure_document(SYSTEM_PROMPT_1_FILE, DEFAULT_PROMPT_URL, "System Prompt 1")
    sp2 = ensure_document(SYSTEM_PROMPT_2_FILE, DEFAULT_PROMPT_URL, "System Prompt 2")
    sp3 = ensure_document(SYSTEM_PROMPT_3_FILE, DEFAULT_PROMPT_URL, "System Prompt 3")
    
    if not (sp1 and sp2 and sp3):
        print("[ERROR] Missing one or more System Prompts. Cannot run the benchmark. Exiting.")
        exit(0)
        
    sys_prompts_dict = {1: sp1, 2: sp2, 3: sp3}

    while True:
        last_profile = config.get("LAST_PROFILE", "")
        
        print("\n" + "-"*50)
        if last_profile and "profiles" in config and last_profile in config["profiles"]:
            p_data = config["profiles"][last_profile]
            print(f"Welcome back! Last used profile: {last_profile}")
            print(f"Current Model: {p_data.get('MODEL_NAME')}")
            print("\nWhat would you like to do?")
            print(" [C] CONTINUE with last profile (Ensures NO repeated targets)")
            print(" [N] Create NEW profile (Starts a fresh target history)")
            print(" [S] Change API SETTINGS for current profile (Key, Model)")
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
            profile_name = input("\nEnter Profile Name (e.g. Default-Profile): ").strip()
            if not profile_name: profile_name = "Default-Profile"
            config = update_api_settings(config, profile_name)

        # Save active profile
        config["LAST_PROFILE"] = profile_name
        save_config(config)

        # Transcripts & Exercises
        save_input = input("\nSave full session transcripts to text files? [y/N]: ").strip().lower()
        save_transcripts = (save_input == 'y')
        
        exercises_text = None
        run_exercises = False
        exercises_input = input("Should the AI perform sensory calibration exercises after each evaluation? [y/N]: ").strip().lower()
        if exercises_input == 'y':
            exercises_text = ensure_document(EXERCISES_LOCAL_FILE, EXERCISES_RAW_URL, "RV Exercises Document")
            if exercises_text:
                run_exercises = True

        # --- NEW: BENCHMARK CONSTANTS CONFIGURATION ---
        effort_input = input("\nEnter FIXED Reasoning Effort for this benchmark [none/low/medium/high] (default: high): ").strip().lower()
        if effort_input not in ["none", "low", "medium", "high"]:
            effort_input = "high"

        profile_data = config["profiles"][profile_name]
        default_temp = get_optimal_temperature(profile_data.get("MODEL_NAME", ""))
        temp_input = input(f"Enter FIXED Temperature for this benchmark (default: {default_temp}): ").strip()
        try:
            fixed_temp = float(temp_input) if temp_input else default_temp
        except ValueError:
            fixed_temp = default_temp
            print(f"[WARNING] Invalid input. Using default temperature: {fixed_temp}")

        # Target count
        try:
            count_input = input("\nHow many targets would you like to process with this System Prompt Benchmark? (default 1): ").strip()
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
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=profile_data["OPENROUTER_API_KEY"],
            timeout=httpx.Timeout(60.0) 
        )

        print(f"\n[INFO] Initializing benchmark of {actual_run_count} targets (Each tested with 3 different System Prompts)...")
        for i, target_path in enumerate(targets_to_run):
            print(f"\n" + "="*50)
            print(f"[INFO] PROCESSING TARGET {i+1} OF {actual_run_count}")
            print("="*50)
            run_sysprompt_benchmark_session(client, profile_data, sys_prompts_dict, exercises_text, target_path, profile_name, save_transcripts, run_exercises, effort_input, fixed_temp)

        if actual_run_count < target_count:
            print(f"\n[INFO] Batch finished! Successfully ran {actual_run_count} out of {target_count} requested targets, because there were no more new targets left in the folder.")
        else:
            print("\n[INFO] Batch finished successfully!")
