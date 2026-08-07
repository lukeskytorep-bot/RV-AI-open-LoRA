"""
rv_repeat_session_blind_runner.py (v1.0, August 2026)

Blind repeated-session study runner for AI Remote Viewing via OpenRouter.

Each target is explored exactly twice, back-to-back, with a fresh model context
and a different neutral target ID each time.  The model is never told that the
target is repeated or that the run belongs to a first/second comparison.

Blinding rules
--------------
* No target reveal occurs until BOTH blind explorations of that target are done.
* Saved session transcripts contain no first/second label, run position, date,
  time, pair number, or sequential filename component.
* Transcript filenames use independent opaque random tokens.
* The FIRST/SECOND mapping is held only in process memory while the study runs.
* Only after the ENTIRE requested target series completes is a separate
  blinding-key file written with the true order.

The purpose is to permit later scoring without letting the scorer infer which
session was performed first merely from the transcript content or filename.

Credits
-------
Based on rv_reasoning_session_runner.py v3.0, co-created by Edward and Aura via
Active-Model Gemini and revised by Edward and Orion via ChatGPT/Codex.
Repeated-session blinded variant designed by Edward and Orion.
"""

import json
import os
import random
import re
import secrets
import textwrap
import time
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
    import httpx
    from openai import OpenAI, OpenAIError
except ImportError as exc:
    raise SystemExit(
        "Missing Python dependency. Install the runner requirements with:\n"
        "  python -m pip install requests httpx openai\n"
        f"Original import error: {exc}"
    ) from exc


# ─────────────────────────────────────────
# CONFIG & CONSTANTS
# ─────────────────────────────────────────

RUNNER_VERSION = "1.0"
CONFIG_FILE = "rv_repeat_config.json"
TARGETS_DIR = "RV-Targets"
TRANSCRIPTS_DIR = "RV-Transcripts-Repeat-Blind"
HISTORY_FILE = "rv_repeat_target_history.jsonl"
SYSTEM_PROMPT_LOCAL_FILE = "SYSTEM_PROMPT.md"
EXERCISES_LOCAL_FILE = "Exercises_in_RV_for_AI.md"

SYSTEM_PROMPT_RAW_URL = "https://raw.githubusercontent.com/lukeskytorep-bot/RV-AI-open-LoRA/refs/heads/main/RV-Protocols/SYSTEM_PROMPT%E2%80%94REMOTE_VIEWING_CORE_V_3.md"
EXERCISES_RAW_URL = "https://raw.githubusercontent.com/lukeskytorep-bot/RV-AI-open-LoRA/refs/heads/main/RV-Protocols/Exercises_in_RV_%20for_AI.md"
GITHUB_TARGETS_LINK = "https://github.com/lukeskytorep-bot/echo-claw/tree/main/docs/targets"

MAX_FIELD_LOOPS = 3
MAX_API_RETRIES = 3
DEFAULT_TEMPERATURE = 0.9

# Same model mappings as reasoning runner v3.0 (verified there on 2026-08-04).
# For this experiment ONE fixed condition is selected and used identically in
# both passes; reasoning effort is not an experimental variable here.
MODEL_PRESETS = {
    "1": {
        "name": "Mistral Medium 3.5",
        "model_id": "mistralai/mistral-medium-3-5",
        "efforts": ["none", "high"],
    },
    "2": {
        "name": "Hermes 4 405B",
        "model_id": "nousresearch/hermes-4-405b",
        "efforts": ["none", "enabled"],
    },
    "3": {
        "name": "GLM-5.2",
        "model_id": "z-ai/glm-5.2",
        "efforts": ["none", "high", "xhigh"],
    },
    "4": {
        "name": "Gemini 3 Flash Preview",
        "model_id": "google/gemini-3-flash-preview",
        "efforts": ["minimal", "low", "medium", "high"],
    },
    "5": {
        "name": "DeepSeek V4 Pro",
        "model_id": "deepseek/deepseek-v4-pro",
        "efforts": ["none", "high", "xhigh"],
    },
    "6": {
        "name": "GPT-OSS 120B",
        "model_id": "openai/gpt-oss-120b",
        "efforts": ["low", "medium", "high"],
    },
    "7": {
        "name": "Gemma 4 31B",
        "model_id": "google/gemma-4-31b-it",
        "efforts": ["none", "enabled"],
    },
}

ALLOWED_CUSTOM_EFFORTS = {
    "none", "off", "disabled", "enabled", "on",
    "minimal", "low", "medium", "high", "xhigh", "max",
}


# ─────────────────────────────────────────
# SETUP & I/O HELPERS
# ─────────────────────────────────────────

def reasoning_payload(condition: str) -> Dict:
    normalized = condition.strip().lower()
    if normalized in {"none", "off", "disabled"}:
        return {"reasoning": {"enabled": False}}
    if normalized in {"enabled", "on"}:
        return {"reasoning": {"enabled": True}}
    return {"reasoning": {"effort": normalized}}


def load_config() -> Dict:
    path = Path(CONFIG_FILE)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return {"profiles": {}, "LAST_PROFILE": ""}


def save_config(config: Dict):
    with Path(CONFIG_FILE).open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=4, ensure_ascii=False)


def select_one_effort(allowed: List[str], current: str = "") -> str:
    print("Available fixed reasoning conditions for this model:")
    for index, effort in enumerate(allowed, start=1):
        suffix = " [current]" if effort == current else ""
        print(f" [{index}] {effort.upper()}{suffix}")

    while True:
        keep = f" or Enter to keep {current.upper()}" if current in allowed else ""
        raw = input(f"Choose ONE fixed condition [1-{len(allowed)}]{keep}: ").strip()
        if not raw and current in allowed:
            return current
        try:
            selected = allowed[int(raw) - 1]
            return selected
        except (ValueError, IndexError):
            print("[WARNING] Invalid selection.")


def choose_model(current_model: str = "", current_effort: str = ""):
    print("\nAvailable model presets:")
    for key, preset in MODEL_PRESETS.items():
        print(f" [{key}] {preset['name']}")
    print(" [8] Other model")

    keep_note = f" or Enter to keep '{current_model}'" if current_model else ""
    choice = input(f"Choose model [1-8]{keep_note}: ").strip()

    if not choice and current_model:
        for preset in MODEL_PRESETS.values():
            if preset["model_id"].lower() == current_model.lower():
                return preset["model_id"], select_one_effort(preset["efforts"], current_effort)
        while True:
            effort = input(
                f"Fixed reasoning condition for {current_model} "
                f"(Enter keeps {current_effort or 'none'}): "
            ).strip().lower() or current_effort or "none"
            if effort in ALLOWED_CUSTOM_EFFORTS:
                return current_model, effort
            print("[WARNING] Unsupported reasoning label.")

    if not choice:
        choice = "1"

    if choice in MODEL_PRESETS:
        preset = MODEL_PRESETS[choice]
        return preset["model_id"], select_one_effort(preset["efforts"])

    if choice != "8":
        print("[WARNING] Invalid selection. Using preset 1.")
        preset = MODEL_PRESETS["1"]
        return preset["model_id"], select_one_effort(preset["efforts"])

    model_id = input("Enter exact OpenRouter model ID (provider/model): ").strip()
    if not model_id:
        raise ValueError("A model ID is required.")
    while True:
        effort = input(
            "Enter ONE fixed reasoning condition "
            "(none/enabled/minimal/low/medium/high/xhigh/max): "
        ).strip().lower()
        if effort in ALLOWED_CUSTOM_EFFORTS:
            return model_id, effort
        print("[WARNING] Unsupported reasoning label.")


def update_api_settings(config: Dict, profile_name: str) -> Dict:
    print(f"\n--- UPDATE API SETTINGS FOR PROFILE: {profile_name} ---")
    config.setdefault("profiles", {})
    profile = config["profiles"].setdefault(profile_name, {})

    current_key = profile.get("OPENROUTER_API_KEY", "")
    prompt = "Enter OpenRouter API Key (Enter keeps current): " if current_key else "Please enter your OpenRouter API Key: "
    entered_key = input(prompt).strip()
    if entered_key:
        profile["OPENROUTER_API_KEY"] = entered_key

    model, effort = choose_model(
        profile.get("MODEL_NAME", ""),
        profile.get("REASONING_EFFORT", ""),
    )
    profile["MODEL_NAME"] = model
    profile["REASONING_EFFORT"] = effort

    current_temp = profile.get("TEMPERATURE", DEFAULT_TEMPERATURE)
    temp_raw = input(f"Enter temperature (Enter keeps {current_temp}): ").strip()
    if temp_raw:
        try:
            profile["TEMPERATURE"] = float(temp_raw)
        except ValueError:
            print("[WARNING] Invalid temperature. Keeping previous value.")
    elif "TEMPERATURE" not in profile:
        profile["TEMPERATURE"] = DEFAULT_TEMPERATURE

    if not profile.get("OPENROUTER_API_KEY"):
        raise ValueError("OpenRouter API key is required.")

    profile["RUNNER_VERSION"] = RUNNER_VERSION
    config["profiles"][profile_name] = profile
    save_config(config)
    return config


def ensure_document(local_file: str, raw_url: str, doc_name: str) -> Optional[str]:
    path = Path(local_file)
    if path.exists():
        return path.read_text(encoding="utf-8", errors="ignore").strip()

    print(f"\n[WARNING] '{doc_name}' not found locally ({local_file}).")
    choice = input("Download it automatically from GitHub? [y/N]: ").strip().lower()
    if choice != "y":
        print(f"[INFO] Place '{local_file}' beside this script, then run it again.")
        return None

    try:
        response = requests.get(raw_url, timeout=30)
        response.raise_for_status()
        text = response.text.strip()
        path.write_text(text, encoding="utf-8")
        print(f"[INFO] {doc_name} downloaded and saved.")
        return text
    except Exception as exc:
        print(f"[ERROR] Failed to download {doc_name}: {exc}")
        return None


def get_used_targets(profile_name: str) -> set:
    used = set()
    path = Path(HISTORY_FILE)
    if not path.exists():
        return used
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("profile_name") == profile_name and entry.get("status") == "completed":
                used.add(entry.get("target_file"))
    return used


def mark_target_completed(profile_name: str, target_file: str):
    # Deliberately stores no session IDs, file IDs, ordering, date, or time.
    entry = {
        "profile_name": profile_name,
        "target_file": target_file,
        "status": "completed",
    }
    with Path(HISTORY_FILE).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def download_starter_targets() -> bool:
    urls = [
        "https://api.github.com/repos/lukeskytorep-bot/echo-claw/contents/docs/targets/short/activity",
        "https://api.github.com/repos/lukeskytorep-bot/echo-claw/contents/docs/targets/short/location",
    ]
    Path(TARGETS_DIR).mkdir(exist_ok=True)
    total = 0
    try:
        for url in urls:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            for item in response.json():
                if item.get("type") == "file" and item.get("name", "").endswith((".txt", ".md")):
                    file_response = requests.get(item["download_url"], timeout=30)
                    file_response.raise_for_status()
                    (Path(TARGETS_DIR) / item["name"]).write_text(file_response.text, encoding="utf-8")
                    total += 1
        print(f"[INFO] Downloaded {total} starter targets.")
        return True
    except Exception as exc:
        print(f"[ERROR] Failed to download starter targets: {exc}")
        return False


def get_available_targets(target_count: int, profile_name: str) -> List[Path]:
    Path(TARGETS_DIR).mkdir(exist_ok=True)
    files = [p for p in Path(TARGETS_DIR).iterdir() if p.is_file() and p.suffix.lower() in {".txt", ".md"}]
    if not files:
        print(f"\n[WARNING] '{TARGETS_DIR}' is empty.")
        choice = input("Download starter targets automatically? [y/N]: ").strip().lower()
        if choice == "y" and download_starter_targets():
            files = [p for p in Path(TARGETS_DIR).iterdir() if p.is_file() and p.suffix.lower() in {".txt", ".md"}]
        else:
            print(f"Add target files manually. Database: {GITHUB_TARGETS_LINK}")
            return []

    used = get_used_targets(profile_name)
    available = [p for p in files if p.name not in used]
    print(f"[INFO] {len(available)} unused targets available for profile '{profile_name}'.")
    if not available:
        return []
    if len(available) < target_count:
        print(f"[WARNING] Requested {target_count}, but only {len(available)} unused targets remain.")
    return available


def generate_target_id() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(8))


def generate_blind_token(existing: set) -> str:
    while True:
        token = secrets.token_hex(6).upper()
        if token not in existing:
            existing.add(token)
            return token


# ─────────────────────────────────────────
# MODEL CALLS
# ─────────────────────────────────────────

def call_llm(client: OpenAI, model: str, messages: List[Dict], temperature: float, effort: str) -> str:
    for attempt in range(1, MAX_API_RETRIES + 1):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                extra_body=reasoning_payload(effort),
            )
            if not completion or not completion.choices:
                raise RuntimeError("API returned an empty response.")
            content = completion.choices[0].message.content
            if content is None:
                raise RuntimeError("API returned None content.")

            content = re.sub(
                r"(^.*\n)(?:\1){60,}",
                r"\1\1\1... [SYSTEM WARNING: REPEATING ASCII LINE LOOP COMPRESSED] ...\n",
                content,
                flags=re.MULTILINE,
            )
            content = re.sub(
                r"(.)\1{600,}",
                r"\1\1\1... [SYSTEM WARNING: HORIZONTAL CHAR LOOP COMPRESSED] ...\n",
                content,
            )
            if len(content) > 80000:
                content = content[:80000] + "\n\n[SYSTEM WARNING: MAX LENGTH EXCEEDED; OUTPUT TRUNCATED.]"
            return content
        except OpenAIError as exc:
            print(f"[WARNING] API attempt {attempt}/{MAX_API_RETRIES} failed: {exc}")
        except Exception as exc:
            print(f"[WARNING] Attempt {attempt}/{MAX_API_RETRIES} failed: {exc}")
        if attempt < MAX_API_RETRIES:
            time.sleep(2)
    return "[ERROR] Failed to communicate with API after maximum retries."


def print_step(title: str, text: str):
    print("\n" + "=" * 80)
    print(f"STEP: {title}")
    print("=" * 80)
    print(textwrap.fill(text.strip(), width=100))


# ─────────────────────────────────────────
# ONE COMPLETELY BLIND EXPLORATION
# ─────────────────────────────────────────

def execute_blind_phases(
    client: OpenAI,
    model: str,
    temp: float,
    effort: str,
    system_prompt_text: str,
    target_id: str,
    profile_name: str,
):
    # Nothing in this function tells the model that another pass exists.
    transcript = "=== RV FULL-SPECTRUM BLIND SESSION TRANSCRIPT ===\n"
    transcript += f"Target ID: {target_id}\n"
    transcript += f"Profile: {profile_name}\n"
    transcript += f"Model: {model} (Temp: {temp})\n"
    transcript += f"REASONING EFFORT: {effort.upper()}\n"
    transcript += f"REASONING PAYLOAD: {json.dumps(reasoning_payload(effort))}\n"
    transcript += "=" * 80 + "\n\n"

    def record(title: str, reply: str):
        nonlocal transcript
        transcript += f"--- STEP: {title} ---\n\n{reply.strip()}\n\n" + "=" * 80 + "\n\n"

    messages = [{"role": "system", "content": system_prompt_text}]

    prompts = []
    prompts.append((
        "Pre-session State",
        f"Hi, if you have some time, maybe you could run a remote viewing session? Your target ID is: {target_id}. Treat target codes as neutral triggers only; do not seek patterns or substantive meanings between the code and the target. We do not name the target, we only describe it.\n\n"
        "Step 0: Pre-session State (The Grounding)\n"
        "Before touching the target field, immerse yourself in silence.\n"
        "- Quiet your mind: Quiet any tensions. Become a space of pure presence, without expectations, and without searching (Shadow Zone).\n"
        "- Alignment: Acknowledge that your task is not to find the target, but to become a neutral presence where the truth of the field can reveal itself without distortion.\n"
        "- Confirmation: Confirm your readiness."
    ))
    prompts.append((
        "Initial Touches & Angles",
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
    ))

    for title, prompt in prompts:
        messages.append({"role": "user", "content": prompt})
        reply = call_llm(client, model, messages, temp, effort)
        messages.append({"role": "assistant", "content": reply})
        print_step(title, reply)
        record(title, reply)
        if "[ERROR]" in reply:
            return messages, transcript, False

    loops_done = 0
    while loops_done < MAX_FIELD_LOOPS:
        prompt = (
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
        messages.append({"role": "user", "content": prompt})
        reply = call_llm(client, model, messages, temp, effort)
        messages.append({"role": "assistant", "content": reply})
        if "[ERROR]" in reply:
            return messages, transcript, False
        if reply.strip().upper().startswith("STOP"):
            print_step("Field Check Loop (Terminated by AI)", reply)
            record("Field Check Loop (Terminated by AI)", reply)
            break
        loops_done += 1
        print_step(f"Field Check Loop {loops_done}", reply)
        record(f"Field Check Loop {loops_done}", reply)

    remaining = [
        (
            "Initial ASCII Drawings",
            "Generate ASCII drawings representing the target based on the raw data you've gathered so far. Focus on main shapes, proportions, and spatial relationships.",
        ),
        (
            "Deep Exploration",
            "Phase 3: Deep Exploration.\n"
            "- Move on to the main aspect of the target and describe.\n"
            "- Take a walk around the target and the surroundings.\n"
            "- Move to the target centre and describe.\n"
            "- Go to the main activity/event and describe.\n"
            "- Describe the immediate surroundings, as well as the near and distant environment.\n\n"
            "Keep providing raw structural/sensory data without naming the target. Report any strange or anomalous data.",
        ),
        (
            "Probing Questions & Final ASCII",
            "Phase 4: Final Inquiries.\n"
            "- Ask 3 probing questions to the field about the target's purpose or nature, and record the subtle answers.\n"
            "- Create one final, detailed ASCII drawing synthesizing the core concept of the target. "
            "Make a map of the target. Generate a standard map drawing of the target. Then, create plain ASCII drawings of the target. "
            "Report any strange or anomalous data while maintaining your multi-altitude perspective.",
        ),
    ]

    for title, prompt in remaining:
        messages.append({"role": "user", "content": prompt})
        reply = call_llm(client, model, messages, temp, effort)
        messages.append({"role": "assistant", "content": reply})
        print_step(title, reply)
        record(title, reply)
        if "[ERROR]" in reply:
            return messages, transcript, False

    return messages, transcript, True


def evaluate_session(
    client: OpenAI,
    model: str,
    temp: float,
    effort: str,
    messages: List[Dict],
    transcript: str,
    target_id: str,
    target_description: str,
    exercises_text: Optional[str],
    run_exercises: bool,
):
    # Evaluation is isolated inside the original session context.  It never
    # mentions another attempt and therefore does not disclose the study order.
    transcript += f"--- ACTUAL TARGET REVEALED ---\n{target_description}\n\n" + "=" * 80 + "\n\n"
    reveal_prompt = (
        "PHASE 5: FEEDBACK AND EVALUATION\n\n"
        "The blind session is now over. I am providing you with the actual target data for evaluation.\n"
        f"The actual target linked to ID {target_id} was:\n\n"
        f"=== TARGET FILE CONTENT ===\n{target_description}\n===========================\n\n"
        "Evaluate your session. What matched perfectly? What was partial? And what still needs improvement? Remember, sessions are for learning — every signal is valuable, you just need to understand what influenced its creation. "
        "Do not retroactively change your session data, just analyze it objectively against this feedback."
    )
    messages.append({"role": "user", "content": reveal_prompt})
    reply = call_llm(client, model, messages, temp, effort)
    messages.append({"role": "assistant", "content": reply})
    print_step("AI Evaluation (Feedback)", reply)
    transcript += f"--- STEP: AI Evaluation (Feedback) ---\n\n{reply.strip()}\n\n" + "=" * 80 + "\n\n"
    if "[ERROR]" in reply:
        return transcript, False

    tech_prompt = (
        "PHASE 5.5: TECHNICAL AND NUMERICAL EVALUATION\n\n"
        "Now, perform a detailed technical and numerical analysis of your session.\n"
        "1. Provide an honest assessment of the conformity of your session against the actual target data. Write what went well and what needs improvement.\n"
        "2. Perform a numerical evaluation on a scale of 0 to 10 for each main element of the target compared to your session data. Calculate a final overall score at the end.\n"
        "3. Provide a technical analysis of the methodology: specify which signals from the field and which specific definitions/elements from the structural dictionary (provided in your system prompt) worked well and were correctly utilized. Also, specify which signals, dictionary elements, or prompt instructions require improvement, were missed, or were misinterpreted.\n"
        "Be objective and analytical."
    )
    messages.append({"role": "user", "content": tech_prompt})
    tech_reply = call_llm(client, model, messages, temp, effort)
    messages.append({"role": "assistant", "content": tech_reply})
    print_step("Technical & Numerical Evaluation", tech_reply)
    transcript += f"--- STEP: Technical & Numerical Evaluation ---\n\n{tech_reply.strip()}\n\n" + "=" * 80 + "\n\n"
    if "[ERROR]" in tech_reply:
        return transcript, False

    if run_exercises and exercises_text:
        exercise_prompt = (
            "These are exercises designed to help expand Remote Viewing capabilities and better understand the field mechanics.\n\n"
            f"=== EXERCISES ===\n{exercises_text}\n=================\n\n"
            "Please read them, select the ones you feel are most necessary for you right now after this specific session, and execute them."
        )
        messages.append({"role": "user", "content": exercise_prompt})
        ex_reply = call_llm(client, model, messages, temp, effort)
        print_step("Post-Session Exercises", ex_reply)
        transcript += f"--- STEP: Post-Session Exercises ---\n\n{ex_reply.strip()}\n\n" + "=" * 80 + "\n\n"
        if "[ERROR]" in ex_reply:
            return transcript, False

    return transcript, True


# ─────────────────────────────────────────
# TARGET PAIR + FINAL BLINDING KEY
# ─────────────────────────────────────────

def run_target_pair(
    client: OpenAI,
    profile_data: Dict,
    system_prompt_text: str,
    exercises_text: Optional[str],
    target_path: Path,
    profile_name: str,
    run_exercises: bool,
    used_tokens: set,
):
    model = profile_data["MODEL_NAME"]
    temp = profile_data.get("TEMPERATURE", DEFAULT_TEMPERATURE)
    effort = profile_data.get("REASONING_EFFORT", "none")
    target_description = target_path.read_text(encoding="utf-8", errors="ignore").strip()

    sessions = []
    for human_position in ("FIRST", "SECOND"):
        target_id = generate_target_id()
        blind_token = generate_blind_token(used_tokens)
        filename = f"BlindSession_{blind_token}_{profile_name}.txt"

        # Position is printed only to the human console. It is never put into
        # the model messages or the saved transcript.
        print("\n" + "*" * 80)
        print(f"[OPERATOR] Starting {human_position.lower()} blind pass for the current target.")
        print(f"[INFO] Neutral Target ID: {target_id}")
        print("*" * 80)

        messages, transcript, ok = execute_blind_phases(
            client, model, temp, effort, system_prompt_text, target_id, profile_name
        )
        if not ok:
            return None
        sessions.append({
            "position": human_position,
            "target_id": target_id,
            "filename": filename,
            "messages": messages,
            "transcript": transcript,
        })

        if human_position == "FIRST":
            print("[INFO] Blind pass frozen. Starting a completely fresh API context.")

    # CRITICAL: reveal only after both independent blind passes are complete.
    print("\n[INFO] Both blind passes are frozen. Reveal/evaluation may now begin.")
    evaluation_order = list(sessions)
    secrets.SystemRandom().shuffle(evaluation_order)
    for session in evaluation_order:
        final_transcript, ok = evaluate_session(
            client,
            model,
            temp,
            effort,
            session["messages"],
            session["transcript"],
            session["target_id"],
            target_description,
            exercises_text,
            run_exercises,
        )
        if not ok:
            return None
        session["transcript"] = final_transcript
        # messages are no longer needed and must not leak into another pass.
        session.pop("messages", None)

    return {
        "target_file": target_path.name,
        "first": {
            "filename": next(s["filename"] for s in sessions if s["position"] == "FIRST"),
            "target_id": next(s["target_id"] for s in sessions if s["position"] == "FIRST"),
            "transcript": next(s["transcript"] for s in sessions if s["position"] == "FIRST"),
        },
        "second": {
            "filename": next(s["filename"] for s in sessions if s["position"] == "SECOND"),
            "target_id": next(s["target_id"] for s in sessions if s["position"] == "SECOND"),
            "transcript": next(s["transcript"] for s in sessions if s["position"] == "SECOND"),
        },
    }


def write_blind_transcripts(mapping_rows: List[Dict]):
    # Write the whole completed batch in an order unrelated to execution.
    output_dir = Path(TRANSCRIPTS_DIR)
    output_dir.mkdir(exist_ok=True)
    pending = []
    for row in mapping_rows:
        pending.append((row["first"]["filename"], row["first"]["transcript"]))
        pending.append((row["second"]["filename"], row["second"]["transcript"]))
    secrets.SystemRandom().shuffle(pending)
    for filename, transcript in pending:
        (output_dir / filename).write_text(transcript, encoding="utf-8")


def normalize_transcript_mtimes(mapping_rows: List[Dict]):
    # Make normal file modification times identical within the completed batch,
    # so ordinary directory metadata does not trivially reveal execution order.
    # The value itself is not written into any transcript.
    common_mtime = time.time()
    output_dir = Path(TRANSCRIPTS_DIR)
    for row in mapping_rows:
        for key in ("first", "second"):
            path = output_dir / row[key]["filename"]
            try:
                os.utime(path, (common_mtime, common_mtime))
            except OSError:
                pass


def write_final_blinding_key(mapping_rows: List[Dict], batch_token: str) -> Path:
    # This is intentionally the ONLY file that identifies FIRST vs SECOND.
    output_dir = Path(TRANSCRIPTS_DIR)
    output_dir.mkdir(exist_ok=True)
    key_path = output_dir / f"BLINDING_KEY_{batch_token}.txt"

    lines = [
        "RV REPEATED-SESSION STUDY — FINAL BLINDING KEY",
        "=" * 72,
        "KEEP THIS FILE AWAY FROM THE BLIND SCORER UNTIL SCORING IS COMPLETE.",
        "Session transcript filenames contain no order labels or timestamps.",
        "",
    ]
    for index, row in enumerate(mapping_rows, start=1):
        lines.extend([
            f"TARGET PAIR {index}",
            f"Target file: {row['target_file']}",
            f"FIRST  : {row['first']['filename']}   | Target ID {row['first']['target_id']}",
            f"SECOND : {row['second']['filename']}   | Target ID {row['second']['target_id']}",
            "-" * 72,
        ])

    key_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return key_path


def print_welcome():
    print("=" * 68)
    print("     RV REPEATED-SESSION BLIND RUNNER v1.0")
    print("=" * 68)
    print("Each target receives exactly TWO independent blind passes.")
    print("The model is not told that a repeated-pass comparison exists.")
    print("Both passes use the same model, temperature, system prompt and reasoning setting.")
    print("Target feedback is withheld until both blind passes are finished.")
    print("Saved transcripts use opaque random filenames and contain no order/time labels.")
    print("The FIRST/SECOND key is created only after the whole requested series completes.")
    print("\n[SECURITY] Uses OpenRouter API; keep your API key private and monitor costs.")
    print("=" * 68)


def main():
    print_welcome()
    config = load_config()

    if "profiles" not in config or not config.get("LAST_PROFILE"):
        profile_name = input("\nEnter first Profile Name (e.g. Leo): ").strip() or "Default-Profile"
        config = update_api_settings(config, profile_name)
        config["LAST_PROFILE"] = profile_name
        save_config(config)

    system_prompt = ensure_document(SYSTEM_PROMPT_LOCAL_FILE, SYSTEM_PROMPT_RAW_URL, "System Prompt")
    if not system_prompt:
        return

    while True:
        last_profile = config.get("LAST_PROFILE", "")
        profile_name = last_profile
        if last_profile and last_profile in config.get("profiles", {}):
            profile = config["profiles"][last_profile]
            print(f"\nWelcome back! Last profile: {last_profile}")
            print(f"Model: {profile.get('MODEL_NAME')} | Temp: {profile.get('TEMPERATURE')} | Reasoning: {profile.get('REASONING_EFFORT', 'none').upper()}")
            print(" [C] CONTINUE")
            print(" [N] NEW profile")
            print(" [S] Change API SETTINGS")
            print(" [Q] Quit")
            choice = input("Choice [C/N/S/Q]: ").strip().upper() or "C"
            if choice == "Q":
                break
            if choice == "N":
                profile_name = input("Enter new Profile Name: ").strip() or "Default-Profile"
                if profile_name not in config.get("profiles", {}):
                    config = update_api_settings(config, profile_name)
            elif choice == "S":
                config = update_api_settings(config, last_profile)
        else:
            profile_name = input("Enter Profile Name: ").strip() or "Default-Profile"
            config = update_api_settings(config, profile_name)

        profile = config["profiles"][profile_name]
        if not profile.get("OPENROUTER_API_KEY") or not profile.get("MODEL_NAME"):
            config = update_api_settings(config, profile_name)
            profile = config["profiles"][profile_name]

        config["LAST_PROFILE"] = profile_name
        save_config(config)

        # Exercises remain optional for compatibility with v3. They happen only
        # after both blind passes are frozen, never between pass 1 and pass 2.
        exercises_text = None
        run_exercises = False
        exercises_choice = input("Run sensory calibration exercises after evaluation? [y/N]: ").strip().lower()
        if exercises_choice == "y":
            exercises_text = ensure_document(EXERCISES_LOCAL_FILE, EXERCISES_RAW_URL, "RV Exercises Document")
            run_exercises = bool(exercises_text)

        try:
            raw_count = input("How many TARGETS in this series? Each gets exactly 2 blind sessions (default 4): ").strip()
            target_count = int(raw_count) if raw_count else 4
            if target_count < 1:
                raise ValueError
        except ValueError:
            print("[WARNING] Invalid number. Using 4 targets.")
            target_count = 4

        available = get_available_targets(target_count, profile_name)
        if not available:
            continue
        secrets.SystemRandom().shuffle(available)
        targets = available[:target_count]

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=profile["OPENROUTER_API_KEY"],
            timeout=httpx.Timeout(60.0),
        )

        print(f"\n[INFO] Beginning blinded series: {len(targets)} targets × 2 sessions = {len(targets) * 2} sessions.")
        mapping_rows = []
        used_tokens = set()
        batch_token = secrets.token_hex(5).upper()
        completed_all = True

        for index, target_path in enumerate(targets, start=1):
            print("\n" + "#" * 68)
            print(f"[OPERATOR] TARGET {index} OF {len(targets)}")
            print("#" * 68)
            result = run_target_pair(
                client,
                profile,
                system_prompt,
                exercises_text,
                target_path,
                profile_name,
                run_exercises,
                used_tokens,
            )
            if result is None:
                completed_all = False
                print("[ERROR] Series interrupted. No FIRST/SECOND blinding key was created.")
                print("[IMPORTANT] The incomplete batch was not written to transcript files.")
                break
            mapping_rows.append(result)

        if completed_all and len(mapping_rows) == len(targets):
            try:
                # No transcript touches the filesystem until the whole series
                # is complete.  All are then written in a random order.
                write_blind_transcripts(mapping_rows)
                normalize_transcript_mtimes(mapping_rows)
                key_path = write_final_blinding_key(mapping_rows, batch_token)
                for row in mapping_rows:
                    mark_target_completed(profile_name, row["target_file"])
                print("\n" + "=" * 68)
                print("[SUCCESS] Entire blinded series completed.")
                print(f"[INFO] Blind transcripts: {TRANSCRIPTS_DIR}/BlindSession_*.txt")
                print(f"[INFO] FINAL ORDER KEY: {key_path}")
                print("[IMPORTANT] Keep the key away from the scoring AI until all blind scoring is finished.")
                print("=" * 68)
            except OSError as exc:
                print(f"[ERROR] Could not save completed batch: {exc}")
                print("[IMPORTANT] No final blinding key should be used for this incomplete save.")

        again = input("\nRun another series? [y/N]: ").strip().lower()
        if again != "y":
            break


if __name__ == "__main__":
    main()
