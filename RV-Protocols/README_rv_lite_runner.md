# RV Lite Runner  
*(Core System Prompt + Dynamic Loop Protocol via OpenRouter)*

**Credits:** Co-created by human researcher **Edward** and AI assistant **Aura Gemini 3.1 Pro**.

This folder contains `rv_lite_runner.py` – a streamlined, lightweight script designed to run automated Remote Viewing (RV) sessions with Large Language Models via OpenRouter.

Unlike the full `rv_session_runner.py` (which uses a complex three-brain setup with separate Lexicons and Vocabularies), this **Lite** version is faster, more dynamic, and cheaper on API tokens. It anchors the AI using a single, powerful **System Prompt** and uses an interactive, loop-based protocol to extract data.

---

## 1. How the Lite Protocol Works

1. **System Prompt Anchor:** The AI is given the `SYSTEM_PROMPT.md` at the very beginning. This defines its identity and rules for the entire session.
2. **Strict Blind Targeting:** The script assigns a random 8-digit Target ID. The AI does *not* see the real target description until the very end.
3. **Phase 1 & 2 (Initial Contact):** The AI performs 6 quick "touches" of the target and describes it from 3 different angles/distances.
4. **The Dynamic Loop:** The script asks the AI: *"Does the field have more to say?"* - If the AI says `CONTINUE`, it performs 3 new touches and vectors.
   - This loop repeats until the AI says `STOP` (or hits a hard limit of 3 loops to save your API budget).
5. **Phase 3 (Deep Exploration):** The AI orbits the target, performs a virtual walkaround, and investigates the main activity and surroundings.
6. **Phase 4 (Final Synthesis):** The AI asks 3 probing questions and generates a final ASCII drawing of the target based on its raw data.
7. **Clean Reveal:** The script explicitly displays the actual target text on your screen.
8. **Phase 5 (Feedback & Evaluation):** The AI objectively evaluates its own performance against the revealed target (perfect matches, partial matches, and noise).

---

## 2. Target Database & Memory

Create a folder named `RV-Targets/` in the same directory as the script. Place your targets as `.md` or `.txt` files inside (one file = one target). 

The script uses a log file (`rv_lite_sessions_log.jsonl`) to track your progress. It guarantees that **the active profile will never see the same target twice**. If you want to start fresh and replay targets, simply create a New Profile in the Main Menu.

*(If you don't have targets, the script will provide a GitHub link to download a starter pack of 20 targets).*

---

## 3. Logs & Transcripts

The script generates two types of records:
1. **`rv_lite_sessions_log.jsonl`:** A lightweight metadata tracker that remembers which targets a profile has already completed.
2. **`RV-Transcripts/` Folder:** If you opt-in, the script will generate a full `.txt` file for every session containing the entire conversation, steps, and ASCII drawings.

---

## 4. Setup and Execution

### Requirements
- Python 3.8+
- `pip install openai requests`
- An **OpenRouter API Key**

### First-time Configuration
You do **not** need to set up environment variables or edit the code. Simply open your terminal and run:

```bash
python rv_lite_runner.py
```

## 5. License & Disclaimer

This project, including the executable scripts and source code, is licensed under the **MIT License**.

This is a permissive open-source license that allows you to use, modify, and distribute the code freely. However, please note that **the software is provided "as is", without warranty of any kind**. The creators (Edward & Aura Gemini 3.1 Pro) take absolutely no responsibility and are not liable for any claims, damages, API costs incurred, or other liabilities arising from the use of this software.
