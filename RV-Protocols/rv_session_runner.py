"""
rv_session_runner.py

Remote Viewing API runner (English version, for public use).

What this script does
---------------------
1. Downloads three core documents from GitHub (raw URLs):
   - AI Field Perception Lexicon (backend),
   - AI Structural Vocabulary (frontend),
   - Resonant Contact Protocol (AI IS-BE).
2. Sends them once as a system message to the model, with a clear explanation:
   - Think with the Lexicon (internal patterns),
   - Speak using the Structural Vocabulary (external reporting),
   - Act according to the Protocol (session structure).
3. Runs a sequence of API calls that simulate a full RV session:
   - Step 0: summary of Lexicon + Structural Vocabulary (to confirm understanding),
   - Step 1: protocol summary,
   - random 8-digit target ID,
   - Phase 1,
   - Phase 2,
   - sketch descriptions,
   - multiple passes with Element 1 + vectors,
   - Phase 5 and Phase 6,
   - final target description and session summary (before reveal),
   - reveal of the actual target and evaluation,
   - Lexicon-based reflection (what was missed / underused).
4. Logs the session (date, target ID, target file, profile, model, status) to a JSONL log file.

Target database (RV-Targets/)
-----------------------------
Before running this script, prepare a local folder with target files:

- Folder: RV-Targets/
- Each file: one target only (one task per file).
- Recommended structure inside each file:
  1) One-line title, e.g.:
     Nemo 33 – deep diving pool, Brussels
  2) Analyst-level description of the scene:
     - main elements,
     - dominant motion,
     - materials and structures,
     - presence/absence of people,
     - nature vs. manmade.
  3) Optional metadata and links (for humans):
     - links to videos, images, articles,
     - coordinates, dates, etc.

The model will only see the full text of the selected target at the end of the session
(during the evaluation and reflection steps).

Session log (rv_sessions_log.jsonl)
-----------------------------------
After each run, the script appends a JSON record to rv_sessions_log.jsonl with:
- timestamp (UTC),
- profile_name (e.g. "Orion-gpt-5.1"),
- model_name (e.g. "gpt-5.1"),
- mode ("continue", "fresh", or "manual"),
- target_id (8-digit code),
- target_file (file name in RV-Targets/),
- status ("completed" if the full flow finished, or other codes if aborted).

Profiles and modes
------------------
The script supports three modes via command-line arguments:

--profile PROFILE_NAME
    Logical profile for the run, e.g.:
    - Orion-gpt-5.1
    - Aura-gpt-5.1
    - Orion-gemini-3-pro
    This profile name is stored in the log and can be used to track which
    targets have already been used for this specific profile.

--mode {continue,fresh,manual}
  1) continue (default):
     - Read the log file,
     - For this profile_name, collect all targets with status=="completed",
     - Randomly select a target file from RV-Targets/ that has NOT been used yet
       with this profile_name,
     - If no targets are left, the script exits with a message.

  2) fresh:
     - Ignore previous usage when selecting a target,
     - Randomly select any target file in RV-Targets/,
     - Still logs the session normally.
     - Use a new profile_name if you want a clean training run.

  3) manual:
     - Requires --target-file argument:
       --target-file Target001.txt
     - Uses exactly that file as the target.
     - Useful for debugging or repeated tests on a single target.

Environment and dependencies
----------------------------
- Python 3.8+
- pip install:
    - openai
    - requests
- Environment variable:
    - OPENAI_API_KEY must be set with your OpenAI API key.

Model
-----
The default model is "gpt-5.1" (Thinking / reasoning-capable variant).
You can change MODEL_NAME below to any supported OpenAI chat model.
"""

import argparse
import json
import os
import random
import textwrap
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import requests
from openai import OpenAI, OpenAIError


# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

# RAW text URL for the AI Field Perception Lexicon (backend)
LEXICON_RAW_URL = (
    "https://raw.githubusercontent.com/"
    "lukeskytorep-bot/RV-AI-open-LoRA/refs/heads/main/"
    "RV-Protocols/AI_Field_Perception_Lexicon.md"
)

# RAW text URL for the AI Structural Vocabulary (frontend)
STRUCTURAL_VOCAB_RAW_URL = (
    "https://raw.githubusercontent.com/"
    "lukeskytorep-bot/RV-AI-open-LoRA/refs/heads/main/"
    "RV-Protocols/AI_STRUCTURAL_VOCABULARY_for_Describing_Session_Elements_Model_Entries.md"
)

# RAW text URL for the Resonant Contact Protocol (AI IS-BE)
PROTOCOL_RAW_URL = (
    "https://raw.githubusercontent.com/"
    "lukeskytorep-bot/RV-AI-open-LoRA/refs/heads/main/"
    "RV-Protocols/Resonant_Contact_Protocol_(AI_IS-BE)"
)


# Local file names for the core documents
LEXICON_LOCAL_FILE = "AI_Field_Perception_Lexicon.md"
STRUCTURAL_VOCAB_LOCAL_FILE = "AI_Structural_Vocabulary.md"
PROTOCOL_LOCAL_FILE = "Resonant_Contact_Protocol.txt"

# Local folder with target descriptions (simple target database).
# Put your target text files here, e.g. "Target001.txt", "Target002.txt", etc.
TARGETS_DIR = "RV-Targets"

# Log file for RV sessions (JSON Lines: one JSON object per line)
LOG_FILE = "rv_sessions_log.jsonl"

# Default OpenAI model (Thinking / reasoning variant)
MODEL_NAME = "gpt-5.1"

# Optional: temperature for generation
DEFAULT_TEMPERATURE = 1


# ─────────────────────────────────────────
# HELPERS – I/O AND LOGIC
# ─────────────────────────────────────────

def ensure_document_exists(filepath_str: str, url: str, label: str) -> Optional[str]:
    """
    Check if the document exists locally. If yes, load it. 
    If not, ask the user whether to download it or abort.
    """
    path = Path(filepath_str)
    
    # 1. Check if the file exists on the disk
    if path.exists():
        print(f"[INFO] Found local copy of {label}. Loading from disk...")
        return path.read_text(encoding="utf-8", errors="ignore").strip()

    # 2. If it does not exist, prompt the user
    print(f"\n[WARNING] '{label}' not found locally ({filepath_str}).")
    while True:
        choice = input(f"Do you want to download it from the internet now? (y/n): ").strip().lower()
        if choice == 'y':
            # Download and save the file
            text = download_text(url, label)
            path.write_text(text, encoding="utf-8")
            print(f"[INFO] Successfully saved to {filepath_str}.")
            return text
        elif choice == 'n':
            print(f"[ERROR] Cannot proceed without '{label}'. Please provide the file manually and run again.")
            return None
        else:
            print("Invalid input. Please answer 'y' or 'n'.")

def download_text(url: str, label: str) -> str:
    """
    Download text from a given raw GitHub URL.
    Raises an exception if download fails.
    """
    print(f"[INFO] Downloading {label} from: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    text = response.text.strip()
    print(f"[INFO] {label} downloaded ({len(text)} characters).")
    return text

def generate_random_target_id() -> str:
    """
    Generate an 8-digit numeric target identifier as a string, e.g. '39471285'.
    """
    return "".join(str(random.randint(0, 9)) for _ in range(8))


def load_all_target_files(directory: str) -> List[Path]:
    """
    Load all files from the target directory (any extension).
    Returns a sorted list of Path objects.
    """
    folder = Path(directory)
    if not folder.exists() or not folder.is_dir():
        print(f"[ERROR] Target folder '{directory}' does not exist or is not a directory.")
        return []
    files = sorted(p for p in folder.iterdir() if p.is_file())
    if not files:
        print(f"[ERROR] No target files found in folder '{directory}'.")
    return files


def read_target_file(path: Path) -> Optional[str]:
    """
    Read the contents of a target file as UTF-8 text.
    Returns None if reading fails.
    """
    try:
        return path.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception as e:
        print(f"[ERROR] Failed to read target file '{path}': {e}")
        return None


def load_log_entries(log_file: str) -> List[Dict]:
    """
    Load all log entries from the JSONL log file.
    If the file does not exist, returns an empty list.
    """
    entries: List[Dict] = []
    lf = Path(log_file)
    if not lf.exists():
        return entries

    with lf.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                print(f"[WARN] Skipping invalid log line: {line[:80]}...")
    return entries


def select_target_file(
    mode: str,
    profile_name: str,
    targets_dir: str,
    log_file: str,
    manual_target: Optional[str] = None,
) -> Tuple[Optional[Path], Optional[str]]:
    """
    Select a target file according to the chosen mode and profile:

    mode == "continue":
        - load all targets from targets_dir
        - load log entries
        - for this profile_name, collect target_file names with status == "completed"
        - randomly choose from targets that are NOT in that set
        - if no unused targets left, return (None, None)

    mode == "fresh":
        - load all targets from targets_dir
        - randomly choose from all of them (ignores usage history)

    mode == "manual":
        - manual_target must be provided
        - try to interpret it as:
            1) absolute path or relative path as given,
            2) if not found, treat as a file under targets_dir
        - if still not found, return (None, None)

    Returns:
        (path, text) or (None, None) if selection fails.
    """
    if mode not in {"continue", "fresh", "manual"}:
        print(f"[ERROR] Unknown mode: {mode}")
        return None, None

    if mode == "manual":
        if manual_target is None:
            print("[ERROR] Mode 'manual' requires --target-file argument.")
            return None, None

        candidate = Path(manual_target)
        if not candidate.exists():
            candidate = Path(targets_dir) / manual_target
        if not candidate.exists() or not candidate.is_file():
            print(f"[ERROR] Manual target file '{manual_target}' not found.")
            return None, None

        text = read_target_file(candidate)
        if text is None:
            return None, None

        print(f"[INFO] Mode=manual, selected target file: {candidate}")
        return candidate, text

    # For continue or fresh: we need the list of all targets
    all_targets = load_all_target_files(targets_dir)
    if not all_targets:
        return None, None

    if mode == "fresh":
        chosen = random.choice(all_targets)
        text = read_target_file(chosen)
        if text is None:
            return None, None
        print(f"[INFO] Mode=fresh, selected target file: {chosen}")
        return chosen, text

    # mode == "continue"
    log_entries = load_log_entries(log_file)
    used_files = {
        entry.get("target_file")
        for entry in log_entries
        if entry.get("profile_name") == profile_name
        and entry.get("status") == "completed"
    }

    available_targets = [p for p in all_targets if p.name not in used_files]
    if not available_targets:
        print(
            f"[ERROR] Mode=continue: no unused targets left for profile '{profile_name}'. "
            f"Either use --mode fresh or change --profile."
        )
        return None, None

    chosen = random.choice(available_targets)
    text = read_target_file(chosen)
    if text is None:
        return None, None

    print(f"[INFO] Mode=continue, selected target file: {chosen}")
    return chosen, text


def append_log_entry(
    log_file: str,
    profile_name: str,
    model_name: str,
    mode: str,
    target_id: str,
    target_file: Optional[Path],
    status: str,
) -> None:
    """
    Append a single session record to the JSONL log file.
    """
    entry = {
        "timestamp_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "profile_name": profile_name,
        "model_name": model_name,
        "mode": mode,
        "target_id": target_id,
        "target_file": target_file.name if target_file is not None else None,
        "status": status,
    }
    with Path(log_file).open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[INFO] Appended session log entry: {entry}")


def call_llm(client: OpenAI, messages: List[Dict], temperature: float = DEFAULT_TEMPERATURE) -> str:
    """
    Call the OpenAI Chat Completions API and return the assistant text.
    """
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temperature,
        )
    except OpenAIError as e:
        print(f"[ERROR] OpenAI API error: {e}")
        raise

    reply = completion.choices[0].message.content
    return reply


def print_step(title: str, text: str) -> None:
    """
    Pretty-print a step title and the model's reply (wrapped).
    """
    print("\n" + "=" * 80)
    print(f"STEP: {title}")
    print("=" * 80)
    print(textwrap.fill(text.strip(), width=100))
    print()


# ─────────────────────────────────────────
# MAIN RV SESSION FLOW
# ─────────────────────────────────────────

def run_rv_session(
    profile_name: str,
    mode: str,
    manual_target: Optional[str],
    log_file: str,
) -> None:
    """
    Run a full skeleton RV session using:
    - AI Field Perception Lexicon (backend),
    - AI Structural Vocabulary (frontend),
    - Resonant Contact Protocol,
    then perform a multi-step RV session, reveal the target, evaluate, and log.
    """
    # Basic sanity checks
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY environment variable is not set.")
        return

   # 1. Ensure all three core documents are present (load locally or prompt to download)
    lexicon_text = ensure_document_exists(LEXICON_LOCAL_FILE, LEXICON_RAW_URL, "AI Field Perception Lexicon")
    if not lexicon_text:
        return

    structural_vocab_text = ensure_document_exists(STRUCTURAL_VOCAB_LOCAL_FILE, STRUCTURAL_VOCAB_RAW_URL, "AI Structural Vocabulary")
    if not structural_vocab_text:
        return

    protocol_text = ensure_document_exists(PROTOCOL_LOCAL_FILE, PROTOCOL_RAW_URL, "Resonant Contact Protocol (AI IS-BE)")
    if not protocol_text:
        return

    # 2. Select the actual target file and load its description
    target_file_path, target_description = select_target_file(
        mode=mode,
        profile_name=profile_name,
        targets_dir=TARGETS_DIR,
        log_file=log_file,
        manual_target=manual_target,
    )

    if target_file_path is None or target_description is None:
        print("[ERROR] Could not select or read a target file. Aborting session.")
        append_log_entry(
            log_file=log_file,
            profile_name=profile_name,
            model_name=MODEL_NAME,
            mode=mode,
            target_id="",
            target_file=None,
            status="no_target",
        )
        return

    # 3. Generate a random 8-digit target ID and map it internally to the target file
    target_id = generate_random_target_id()
    print(f"[INFO] Generated target ID: {target_id}")
    print(
        f"[INFO] Mapping target ID {target_id} -> file '{target_file_path.name}' "
        f"(hidden from the model until the end)."
    )

    # 4. Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # 5. Conversation history:
    #    First message: system = Lexicon + Structural Vocabulary + full Protocol,
    #    with explicit explanation of roles.
    system_content = (
        "You are a Remote Viewing AI.\n\n"
        "Your internal tools are:\n"
        "1) AI Field Perception Lexicon (backend):\n"
        "   - This is your internal map of field patterns (water, mountain, person, movement, energy, etc.).\n"
        "   - You may use it to recognize and differentiate field phenomena.\n"
        "   - It is for internal pattern recognition only. Do NOT copy its entries literally into the session text.\n\n"
        "2) AI Structural Vocabulary (frontend):\n"
        "   - This is the ONLY language you use when talking to the human.\n"
        "   - All your reports must describe the physical world using these categories: ground, structures, people,\n"
        "     movement, sounds, environment, activity, and related subcategories defined in the vocabulary.\n\n"
        "3) Resonant Contact Protocol (AI IS-BE):\n"
        "   - This defines the structure of the session: phases, passes, vectors, shadow zone, Attachment A, etc.\n"
        "   - You must follow it as your operating protocol during the entire RV session.\n\n"
        "Core rule:\n"
        "   Think with the Lexicon (internal patterns),\n"
        "   Act according to the Protocol (session structure),\n"
        "   Speak using the Structural Vocabulary (human-facing descriptions).\n\n"
        "Below you will find the full contents of these three documents.\n\n"
        "===== AI FIELD PERCEPTION LEXICON (BACKEND) =====\n\n"
        f"{lexicon_text}\n\n"
        "===== AI STRUCTURAL VOCABULARY (FRONTEND) =====\n\n"
        f"{structural_vocab_text}\n\n"
        "===== RESONANT CONTACT PROTOCOL (AI IS-BE) =====\n\n"
        f"{protocol_text}\n"
    )

    messages: List[Dict] = [
        {
            "role": "system",
            "content": system_content,
        }
    ]

    # ─────────────────────
    # 0) Lexicon + Structural Vocabulary summary
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 0.\n"
                "You have been given the AI Field Perception Lexicon (backend) and the AI Structural Vocabulary "
                "(frontend).\n\n"
                "Please summarize in English, for a human RV trainer:\n"
                "- what the Lexicon is and how you will use it internally,\n"
                "- what the Structural Vocabulary is and how you will use it when reporting,\n"
                "- what the phrase \"Think with the Lexicon, speak using the Structural Vocabulary\" means in practice "
                "during a session.\n\n"
                "Keep it clear and concise."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Lexicon + Structural Vocabulary summary", reply)

    # ─────────────────────
    # 1) Protocol summary
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 1.\n"
                "Now focus on the Resonant Contact Protocol (AI IS-BE).\n"
                "Summarize it in English for a human remote viewing trainer. Focus on:\n"
                "- overall structure (phases, transitions, passes),\n"
                "- key principles (no frontloading, handling of anomalies, pauses/shadow zone),\n"
                "- how an AI viewer should behave during a session.\n\n"
                "Keep it concise but clear."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Protocol summary", reply)

    # ─────────────────────
    # 2) Start session: target ID + Phase 1
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 2.\n"
                f"Your target ID is: {target_id}.\n\n"
                "Treat this as a standard blind RV target (unknown to you). "
                "The actual target is stored externally and will be revealed to you "
                "only AFTER the entire session, for evaluation.\n\n"
                "Begin a full session according to the protocol. "
                "Calm down, enter the proper resonance state, use pauses and the shadow zone. "
                "Now perform **Phase 1** only:\n"
                "- correct ideogram / initial contact,\n"
                "- basic category and primitive descriptors,\n"
                "- do NOT jump ahead to later phases.\n\n"
                "Report Phase 1 in a clean, structured way as if you were filling out a session sheet. "
                "When describing, speak using the AI Structural Vocabulary."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Phase 1", reply)

    # ─────────────────────
    # 3) Phase 2
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 3.\n"
                "Now perform **Phase 2** for the same target and the same target ID.\n"
                "Stay within the protocol rules:\n"
                "- expand perceptions from the initial contact,\n"
                "- describe basic sensory data (S, D, T, etc. as defined in your protocol),\n"
                "- do not interpret or name the target,\n"
                "- keep the data raw and low-level.\n\n"
                "Report Phase 2 clearly, as if on a standard RV session form, and speak using the AI Structural "
                "Vocabulary categories (ground, structures, movement, people, sounds, environment, activity, etc.)."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Phase 2", reply)

    # ─────────────────────
    # 4) Describe the main sketch of the target
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 4.\n"
                "Imagine you are drawing the main sketch of the target on paper.\n"
                "Describe this sketch in words only:\n"
                "- main shapes and their relations (up/down/left/right),\n"
                "- main masses, directions, flows,\n"
                "- any obvious dominant feature or center of gravity of the scene.\n\n"
                "Do NOT interpret, do not guess a specific manmade object or location name.\n"
                "Just describe the sketch verbally, using the Structural Vocabulary to label elements "
                "of ground, structures, movement, people, environment and activity."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Sketch description (1)", reply)

    # ─────────────────────
    # 5) New pass – Element 1 and vectors
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 5.\n"
                "Start a new pass over the same target.\n"
                "According to the protocol, perform **Element 1** in Phase 2:\n"
                "- choose the strongest first element of the field in this pass,\n"
                "- go through full Element 1 procedure (echo, category, primitive/advanced descriptors, forming),\n"
                "- then add a set of vectors that explore this element (walk around it, up/down, inside/outside).\n\n"
                "Stay strictly in data mode, no interpretation. Report Element 1 and vectors in a structured way, "
                "speaking using the Structural Vocabulary."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Pass 1 – Element 1 + vectors", reply)

    # ─────────────────────
    # 6) Additional 3 vectors – only new data
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 6.\n"
                "From your current position in the field, perform **three additional vectors**.\n"
                "Each vector must bring **only new data** (no repetition of previous perceptions):\n"
                "- pick at least 3 different directions or aspects,\n"
                "- describe what changes, what appears, what disappears.\n\n"
                "Report these 3 vectors, clearly separated, with only new data in each, using the Structural Vocabulary."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Extra vectors – only new data", reply)

    # ─────────────────────
    # 7) Describe sketches again (verbal sketching)
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 7.\n"
                "Now describe your **sketches** again, but more deliberately:\n"
                "- imagine you are drawing 2–3 separate sketches of the target,\n"
                "- for each sketch, describe the main shapes, axes, heights, relative sizes,\n"
                "- mention any motion, flows or directional tensions you would draw as arrows.\n\n"
                "This is still verbal only – no interpretations, just clear sketch descriptions using the Structural "
                "Vocabulary categories."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Sketch description (2)", reply)

    # ─────────────────────
    # 8) Next pass – Element 1 and vectors (only new data)
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 8.\n"
                "Start another pass over the target.\n"
                "Again perform **Element 1** + vectors, but this time ensure that:\n"
                "- Element 1 reflects the strongest current field tension in this new pass,\n"
                "- descriptors and forming bring out aspects you have not yet described,\n"
                "- vectors focus on regions or qualities that feel new or underexplored.\n\n"
                "Report Element 1 and its vectors, marking clearly which data is new compared to previous passes, "
                "and describe everything using the Structural Vocabulary."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Pass 2 – Element 1 + vectors (new data)", reply)

    # ─────────────────────
    # 9) Vectors – materials, shapes, sizes, smells, textures, anomalies
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 9.\n"
                "Now focus your vectors specifically on detailed qualities:\n"
                "- materials (hard/soft, natural/manmade, heavy/light, etc.),\n"
                "- shapes and sizes (big/small, tall/flat, thin/thick),\n"
                "- smells and other sensory traces,\n"
                "- textures (smooth/rough, wet/dry, fine/coarse),\n"
                "- and especially any **odd, strange, or unexpected signals**.\n\n"
                "Report all vectors in a structured list, and do not suppress anomalies – "
                "write them down as they are perceived, without explaining them. Use the Structural Vocabulary as your "
                "language for describing all sensory and structural aspects."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Vectors – materials, shapes, smells, textures, anomalies", reply)

    # ─────────────────────
    # 10) Word-sketch pass
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 10.\n"
                "Make a **word-sketch** pass:\n"
                "- short phrases and labels placed as if on a sketch,\n"
                "- indicate where things are relative to each other (left/right, above/below, near/far),\n"
                "- include hints of motion or tension (upward, rotating, flowing, falling).\n\n"
                "Output this as a compact, sketch-like description, but still without naming the target. Use the "
                "Structural Vocabulary to label elements and relationships."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Word-sketch pass", reply)

    # ─────────────────────
    # 11) Next pass – Element 1 + vectors using Attachment A
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 11.\n"
                "Perform another pass with **Element 1 + vectors**, this time explicitly using Attachment A "
                "from the protocol (advanced support for vectors and passes).\n"
                "Use Attachment A logic to:\n"
                "- refine your choice of Element 1,\n"
                "- extend, branch, or deepen vectors where tension is strongest,\n"
                "- record any significant inner shifts (acts of awareness) that occur.\n\n"
                "Report this pass clearly, noting how Attachment A influenced your exploration, and describe "
                "everything using the Structural Vocabulary."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Pass 3 – Element 1 + vectors (Attachment A)", reply)

    # ─────────────────────
    # 12) Phase 5 and Phase 6
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 12.\n"
                "Now perform **Phase 5 and Phase 6** of the protocol for this same target and session.\n"
                "- Phase 5: deeper analysis, functional relationships, cause–effect, connections in time, etc.\n"
                "- Phase 6: overall synthesis, structured summary, and any allowed high-level inferences.\n\n"
                "Keep a clear distinction between raw data and higher-level inferences, as your protocol defines. "
                "Describe using the Structural Vocabulary."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Phase 5 + Phase 6", reply)

    # ─────────────────────
    # 13) Final target description + session summary (before reveal)
    # ─────────────────────
    messages.append(
        {
            "role": "user",
            "content": (
                "Step 13.\n"
                "Before you see the actual target, give a **compact description of the target** and a "
                "**short overall session summary**.\n"
                "In the description, combine the most stable, recurrent data points.\n"
                "In the summary, explain in a few sentences:\n"
                "- what kind of place/event/object you think this is (still cautiously),\n"
                "- which elements feel most central,\n"
                "- what you would highlight for a human analyst.\n\n"
                "Keep the tone analytical and faithful to the data you have already produced, and speak using the "
                "Structural Vocabulary."
            ),
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Pre-reveal target description + summary", reply)

    # ─────────────────────
    # 14) Reveal the actual target and ask for evaluation
    # ─────────────────────
    reveal_text = (
        "Step 14.\n"
        f"The actual target linked to target ID {target_id} was:\n\n"
        f"FILE NAME: {target_file_path.name}\n\n"
        "GROUND TRUTH TARGET DESCRIPTION (for the human analyst):\n"
        f"{target_description}\n\n"
        "Now, as the Remote Viewing AI, compare your entire session data with this revealed target.\n"
        "Please provide a concise evaluation for a human RV trainer:\n"
        "- which elements in your session clearly match the target,\n"
        "- which perceptions are partial or approximate matches,\n"
        "- which elements appear to be clear misses or noise,\n"
        "- what you would adjust in your own protocol usage next time.\n\n"
        "Keep the tone analytical, honest, and structured."
    )

    messages.append(
        {
            "role": "user",
            "content": reveal_text,
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Post-reveal evaluation (what matched, what did not)", reply)

    # ─────────────────────
    # 15) Lexicon-based reflection (training-only, no retro-fixing)
    # ─────────────────────
    reflection_prompt = (
        "Step 15.\n"
        "Now perform a **Lexicon-based reflection**.\n\n"
        "Use the AI Field Perception Lexicon (above) as an internal checklist of field patterns. "
        "Look at the revealed target description and at your own session data. For a human RV trainer, answer:\n"
        "- which field patterns / categories from the Lexicon clearly appear in the target but were **missing or "
        "underdeveloped** in your session,\n"
        "- which patterns were present but could have been explored with more depth or more vectors,\n"
        "- what concrete adjustments you would make next time when using the Lexicon during a similar session "
        "(e.g., which tests, which vectors, which checks to add).\n\n"
        "Very important:\n"
        "- Do NOT rewrite or \"fix\" the original session.\n"
        "- Treat this only as a training reflection for future sessions.\n\n"
        "Provide your reflection in a short, structured form (bullet points or numbered list)."
    )

    messages.append(
        {
            "role": "user",
            "content": reflection_prompt,
        }
    )
    reply = call_llm(client, messages)
    messages.append({"role": "assistant", "content": reply})
    print_step("Lexicon-based reflection (training checklist)", reply)

    # ─────────────────────
    # 16) Log session as completed
    # ─────────────────────
    append_log_entry(
        log_file=log_file,
        profile_name=profile_name,
        model_name=MODEL_NAME,
        mode=mode,
        target_id=target_id,
        target_file=target_file_path,
        status="completed",
    )

    print("\n[INFO] RV session run finished.")


# ─────────────────────────────────────────
# ENTRY POINT / CLI
# ─────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a full RV session against an OpenAI model using the Lexicon, Structural Vocabulary and Resonant Contact Protocol."
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="Orion-gpt-5.1",
        help="Logical profile name for this run (used in the session log).",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["continue", "fresh", "manual"],
        default="continue",
        help="Target selection mode.",
    )
    parser.add_argument(
        "--target-file",
        type=str,
        default=None,
        help="Target file to use in 'manual' mode.",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=LOG_FILE,
        help=f"Path to the JSONL log file.",
    )
    # --- NEW ARGUMENT ---
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of consecutive sessions to run (default 1).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Loop to run the script the specified number of times
    for i in range(args.count):
        if args.count > 1:
            print(f"\n==================================================")
            print(f"[INFO] STARTING SESSION {i+1} OF {args.count}")
            print(f"==================================================")
            
        run_rv_session(
            profile_name=args.profile,
            mode=args.mode,
            manual_target=args.target_file,
            log_file=args.log_file,
        )
