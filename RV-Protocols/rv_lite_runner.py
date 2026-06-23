"""
rv_lite_runner.py

Remote Viewing "Lite" Runner via OpenRouter.
Uses a core System Prompt instead of full Lexicon/Vocab, 
featuring a dynamic, loop-based exploration protocol.

Credits
-------
Co-created by human researcher Edward and AI assistant Aura  Gemini 3.1 Pro.

What this script does
---------------------
1. Initial Setup: Interactively prompts for your OpenRouter API key and preferred model. It automatically suggests optimal temperatures (e.g., 1.5 for Gemma 4, 1.1 for DeepSeek, 1.0 default) and saves settings to rv_config.json.
2. Core System Prompt: Checks for and downloads SYSTEM_PROMPT.md from GitHub if missing. This acts as the main behavioral anchor for the AI.
3. Target Management: Checks the RV-Targets/ folder. Tracks which targets have already been completed by your specific Profile Name to avoid accidental repetitions.
4. Blind Protocol Execution:
   - Generates a random 8-digit blind Target ID.
   - Initial Touches: Asks the AI for 6 quick structural touches and 3 angles.
   - Dynamic Loop: Asks the "field" if there is more data to reveal. If yes, it triggers more touches/vectors (loops up to 3 times to prevent infinite API usage).
   - Deep Exploration: Commands virtual orbiting, walkarounds, and environmental/activity scans.
   - Synthesizing: Requests ASCII drawings and 3 probing questions.
5. Feedback Phase: Only after the session is complete does the script reveal the actual target file's content to the AI for objective evaluation.
6. Logging & Transcripts: Records session outcomes in rv_lite_sessions_log.jsonl and optionally saves full text transcripts to the RV-Transcripts/ folder.
"""

import os
import json
import random
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

import requests
from openai import OpenAI, OpenAIError

# ─────────────────────────────────────────
# CONFIG & CONSTANTS
# ─────────────────────────────────────────

CONFIG_FILE = "rv_config.json"
TARGETS_DIR = "RV-Targets"
TRANSCRIPTS_DIR = "RV-Transcripts"
LOG_FILE = "rv_lite_sessions_log.jsonl"
SYSTEM_PROMPT_LOCAL_FILE = "SYSTEM_PROMPT.md"
SYSTEM_PROMPT_RAW_URL = "https://raw.githubusercontent.com/lukeskytorep-bot/RV-AI-open-LoRA/refs/heads/main/RV-Protocols/SYSTEM_PROMPT%E2%80%94REMOTE_VIEWING_CORE_V_2.md"
GITHUB_TARGETS_LINK = "https://github.com/lukeskytorep-bot/echo-claw/tree/main/docs/targets"

# Maximum number of times the "Is there more data?" loop can run to prevent infinite API usage
MAX_FIELD_LOOPS = 3

# ─────────────────────────────────────────
# SETUP & I/O HELPERS
# ─────────────────────────────────────────

def get_optimal_temperature(model_name: str) -> float:
    """Returns the optimal temperature based on the selected model architecture."""
    model_lower = model_name.lower()
    if "gemma-4" in model_lower:
        return 1.5
    elif "deepseek" in model_lower:
        return 1.1
    return 1.0

def setup_config() -> Dict:
    """Load config file or ask user for setup if it doesn't exist."""
    config_path = Path(CONFIG_FILE)
    
    # If config already exists, load it and ensure TEMPERATURE is present
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Retrofit older config files that lack the TEMPERATURE setting
        if "TEMPERATURE" not in config:
            optimal_temp = get_optimal_temperature(config.get("MODEL_NAME", ""))
            config["TEMPERATURE"] = optimal_temp
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)
        return config
    
    # First-time setup
    print("\n" + "="*50)
    print(" INITIAL SETUP: RV LITE RUNNER")
    print("="*50)
    print("It looks like this is your first time running the script.")
    api_key = input("Please enter your OpenRouter API Key: ").strip()
    
    default_model = "google/gemma-4-31b-it"
    model_input = input(f"Enter model ID to use (Press Enter for '{default_model}'): ").strip()
    model_name = model_input if model_input else default_model

    # Dynamic temperature handling
    optimal_temp = get_optimal_temperature(model_name)
    print(f"\n[INFO] For the model '{model_name}', the recommended temperature is {optimal_temp}.")
    temp_input = input(f"Enter a custom temperature or press Enter to keep {optimal_temp}: ").strip()
    
    try:
        final_temp = float(temp_input) if temp_input else optimal_temp
    except ValueError:
        print(f"[WARNING] Invalid input. Defaulting to recommended temperature: {optimal_temp}.")
        final_temp = optimal_temp

    config = {
        "OPENROUTER_API_KEY": api_key,
        "MODEL_NAME": model_name,
        "TEMPERATURE": final_temp
    }
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
        
    print(f"[INFO] Configuration saved to {CONFIG_FILE}. You can edit this file later to change settings.")
    return config

def ensure_system_prompt() -> Optional[str]:
    """Check if System Prompt exists locally. If not, download it."""
    path = Path(SYSTEM_PROMPT_LOCAL_FILE)
    if path.exists():
        print("[INFO] System Prompt found locally.")
        return path.read_text(encoding="utf-8", errors="ignore").strip()

    print(f"\n[WARNING] System Prompt not found locally.")
    print(f"[INFO] Downloading from: {SYSTEM_PROMPT_RAW_URL}")
    try:
        response = requests.get(SYSTEM_PROMPT_RAW_URL, timeout=30)
        response.raise_for_status()
        text = response.text.strip()
        path.write_text(text, encoding="utf-8")
        print("[INFO] System Prompt downloaded and saved.")
        return text
    except Exception as e:
        print(f"[ERROR] Failed to download System Prompt: {e}")
        return None

def get_used_targets(profile_name: str) -> set:
    """Read the log file and return a set of target filenames already completed by this profile."""
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

def get_available_targets(session_count: int, profile_name: str, fresh_start: bool) -> List[Path]:
    """Check directory for targets, filter out used ones (unless fresh_start), and return a list."""
    Path(TARGETS_DIR).mkdir(exist_ok=True)
    all_files = [p for p in Path(TARGETS_DIR).iterdir() if p.is_file() and p.suffix in {'.txt', '.md'}]
    
    if not all_files:
        print("\n" + "!"*50)
        print(f"[WARNING] No target files found in '{TARGETS_DIR}/' folder.")
        print(f"You can download 20 starter targets from here:")
        print(f"--> {GITHUB_TARGETS_LINK}")
        print("!"*50 + "\n")
        return []

    if fresh_start:
        available = all_files
        print("[INFO] Fresh start mode: All targets in the folder are available.")
    else:
        used_files = get_used_targets(profile_name)
        available = [p for p in all_files if p.name not in used_files]
        print(f"[INFO] Continue mode: Found {len(all_files)} total targets, {len(used_files)} already used by profile '{profile_name}'. {len(available)} available.")

    if len(available) < session_count:
        if len(available) == 0:
            print(f"\n[ERROR] No unused targets left for profile '{profile_name}'. Please add more files or choose 'Fresh Start'.")
            return []
        else:
            print(f"\n[WARNING] You requested {session_count} sessions, but only {len(available)} unused targets are available. Will run {len(available)} sessions.")

    return available

def generate_target_id() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(8))

def call_llm(client: OpenAI, model: str, messages: List[Dict], temperature: float) -> str:
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return completion.choices[0].message.content
    except OpenAIError as e:
        print(f"[ERROR] API error: {e}")
        raise

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
# MAIN SESSION LOGIC
# ─────────────────────────────────────────

def run_lite_session(client: OpenAI, config: Dict, system_prompt_text: str, target_path: Path, profile_name: str, save_transcripts: bool):
    target_id = generate_target_id()
    model = config["MODEL_NAME"]
    temp = config.get("TEMPERATURE", 1.0)
    
    target_description = target_path.read_text(encoding="utf-8", errors="ignore").strip()
    
    print(f"[INFO] Starting session for Target ID: {target_id} (Hidden file: {target_path.name}) | Temp: {temp}")

    # Initialize transcript content
    transcript_content = f"=== RV LITE SESSION TRANSCRIPT ===\n"
    transcript_content += f"Target ID: {target_id}\n"
    transcript_content += f"Profile: {profile_name}\n"
    transcript_content += f"Model: {model}\n"
    transcript_content += f"Temperature: {temp}\n"
    transcript_content += f"Date (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}Z\n"
    transcript_content += "="*80 + "\n\n"

    def record_to_transcript(title: str, ai_reply: str):
        nonlocal transcript_content
        transcript_content += f"--- STEP: {title} ---\n\n"
        transcript_content += f"{ai_reply.strip()}\n\n"
        transcript_content += "="*80 + "\n\n"

    # Initialize messages with System Prompt
    messages = [
        {"role": "system", "content": system_prompt_text}
    ]

    # STEP 1: Core Touch & Describe Protocol
    step1_prompt = (
        f"Your target ID is: {target_id}.\n\n"
        "Phase 1: Perform 6 quick touches of the target in different places and provide a short description of each touch.\n"
        "Phase 2: Describe the target from a minimum of 3 different angles and distances. Provide new structural and sensory data each time.\n\n"
        "Rules: Do NOT guess or name the target. Provide raw data only. Report any strange or anomalous data."
    )
    messages.append({"role": "user", "content": step1_prompt})
    reply = call_llm(client, model, messages, temp)
    messages.append({"role": "assistant", "content": reply})
    print_step("Initial Touches & Angles", reply)
    record_to_transcript("Initial Touches & Angles", reply)

    # STEP 2: The Loop - Ask the field if there is more
    loops_done = 0
    while loops_done < MAX_FIELD_LOOPS:
        loop_prompt = (
            "Check if the field wants to reveal more data (is there anything left to add?).\n"
            "If YES: output exactly 'CONTINUE' on the first line, then perform 3 new touches and 3 new vectors/angles, reporting new data.\n"
            "If NO: output exactly 'STOP' on the first line, and briefly summarize what you have so far."
        )
        messages.append({"role": "user", "content": loop_prompt})
        reply = call_llm(client, model, messages, temp)
        messages.append({"role": "assistant", "content": reply})
        
        if reply.strip().upper().startswith("STOP"):
            print_step(f"Field Check Loop (Terminated by AI)", reply)
            record_to_transcript(f"Field Check Loop (Terminated by AI)", reply)
            break
        else:
            print_step(f"Field Check Loop {loops_done + 1} (Continuing)", reply)
            record_to_transcript(f"Field Check Loop {loops_done + 1} (Continuing)", reply)
            loops_done += 1

    if loops_done == MAX_FIELD_LOOPS:
        print("[INFO] Reached maximum field loops. Moving to next step.")

    # STEP 3: ASCII Drawings
    step3_prompt = "Generate ASCII drawings representing the target based on the raw data you've gathered so far. Focus on main shapes, proportions, and spatial relationships."
    messages.append({"role": "user", "content": step3_prompt})
    reply = call_llm(client, model, messages, temp)
    messages.append({"role": "assistant", "content": reply})
    print_step("Initial ASCII Drawings", reply)
    record_to_transcript("Initial ASCII Drawings", reply)

    # STEP 4: Deep Exploration (Orbit, Walk, Activity, Surroundings)
    step4_prompt = (
        "Phase 3: Deep Exploration.\n"
        "- Orbit the target close and far.\n"
        "- Take a virtual walk around the target.\n"
        "- Go to the main activity/event happening here and describe it.\n"
        "- Describe the immediate surroundings and environment.\n\n"
        "Keep providing raw structural/sensory data without naming the target."
    )
    messages.append({"role": "user", "content": step4_prompt})
    reply = call_llm(client, model, messages, temp)
    messages.append({"role": "assistant", "content": reply})
    print_step("Deep Exploration (Orbit, Activity, Surroundings)", reply)
    record_to_transcript("Deep Exploration (Orbit, Activity, Surroundings)", reply)

    # STEP 5: Probing Questions & Final ASCII
    step5_prompt = (
        "Phase 4: Final Inquiries.\n"
        "- Ask 3 probing questions to the field about the target's purpose or nature, and record the subtle answers.\n"
        "- Create one final, detailed ASCII drawing synthesizing the core concept of the target."
    )
    messages.append({"role": "user", "content": step5_prompt})
    reply = call_llm(client, model, messages, temp)
    messages.append({"role": "assistant", "content": reply})
    print_step("Probing Questions & Final ASCII", reply)
    record_to_transcript("Probing Questions & Final ASCII", reply)

    # STEP 6: Reveal & Evaluate (FEEDBACK PHASE)
    reveal_prompt = (
        "PHASE 5: FEEDBACK AND EVALUATION\n\n"
        "The blind session is now over. I am providing you with the actual target data for evaluation.\n"
        f"The actual target linked to ID {target_id} was:\n\n"
        f"=== TARGET FILE CONTENT ===\n"
        f"{target_description}\n"
        f"===========================\n\n"
        "Evaluate your session. What matched perfectly? What was partial? What was noise? "
        "Do not retroactively change your session data, just analyze it objectively against this feedback."
    )
    messages.append({"role": "user", "content": reveal_prompt})
    reply = call_llm(client, model, messages, temp)
    print_step("Target Reveal & Evaluation (Feedback)", reply)
    record_to_transcript("Target Reveal & Evaluation (Feedback)", reply)

    # Save transcript if requested
    if save_transcripts:
        Path(TRANSCRIPTS_DIR).mkdir(exist_ok=True)
        transcript_path = Path(TRANSCRIPTS_DIR) / f"Session_{target_id}_{profile_name}.txt"
        transcript_path.write_text(transcript_content, encoding="utf-8")
        print(f"[INFO] Full session transcript saved to: {transcript_path}")

    # Log the session metadata
    log_session(profile_name, model, target_id, target_path.name)

# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("\n==================================================")
    print("        REMOTE VIEWING LITE RUNNER")
    print("==================================================\n")

    # 1. Setup config (API key, Model, Temperature)
    config = setup_config()
    
    # 2. Get system prompt
    system_prompt = ensure_system_prompt()
    if not system_prompt:
        exit(1)

    # 3. Ask for Profile Name and Continue/Fresh mode
    profile_input = input("\nEnter Profile Name (e.g. Lite-Gemma): ").strip()
    profile_name = profile_input if profile_input else "Lite-Gemma"

    print("\nHow would you like to select targets?")
    print(" [C] Continue (Skip targets this profile has already completed)")
    print(" [F] Fresh (Ignore history, use any target in the folder)")
    mode_input = input("Choice [C/F]: ").strip().lower()
    fresh_start = (mode_input == 'f')
    
    # 4. Ask about saving full transcripts
    print("\nWould you like to save full session transcripts to text files?")
    save_input = input("Choice [y/N]: ").strip().lower()
    save_transcripts = (save_input == 'y')
        
    # 5. Ask how many sessions to run
    try:
        count_input = input("\nHow many sessions would you like to run? (default 1): ").strip()
        session_count = int(count_input) if count_input else 1
    except ValueError:
        print("[ERROR] Invalid number. Defaulting to 1.")
        session_count = 1

    # 6. Check and filter targets
    available_targets = get_available_targets(session_count, profile_name, fresh_start)
    if not available_targets:
        exit(1)
        
    # Shuffle targets to ensure random selection
    random.shuffle(available_targets)
    targets_to_run = available_targets[:session_count]

    # 7. Initialize Client
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config["OPENROUTER_API_KEY"],
    )

    # 8. Run the loop
    print(f"\n[INFO] Starting {len(targets_to_run)} sessions...")
    for i, target_path in enumerate(targets_to_run):
        print(f"\n" + "="*50)
        print(f"[INFO] RUNNING SESSION {i+1} OF {len(targets_to_run)}")
        print("="*50)
        run_lite_session(client, config, system_prompt, target_path, profile_name, save_transcripts)

    print("\n[INFO] All requested sessions finished successfully.")
