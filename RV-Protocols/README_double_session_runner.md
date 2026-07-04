# RV Double Session Runner
**(Advanced Cross-Verification Protocol)**

**Credits:** Co-created by human researcher **Edward** and **Aura via Active-Model Gemini 3.1 Pro**.

This folder contains `double_session_runner.py` – a highly advanced, experimental script designed to test the stability, consistency, and accuracy of Large Language Models (LLMs) in Remote Viewing. 

Instead of a standard single run, this script executes a **Double Session** on the exact same target. It completely isolates the AI's memory between runs to ensure a sterile environment, preventing cross-contamination of data, and forces the model to numerically score its own performance.

---

## 1. How the Double Session Protocol Works

To ensure the AI is truly tested without bias or memory retention, the script orchestrates the session in the following sequence:

1. **Session A (Initialization):** The script selects a target, assigns it a random 8-digit ID, and guides the AI through the blind exploration phases (Initial Touches, Dynamic Loops, Deep Exploration, and ASCII generation).
2. **Memory Freeze:** Instead of revealing the target, the script "freezes" the entire conversation history of Session A in the local Python memory.
3. **Context Wipe & Session B:** The AI's context window is completely wiped clean. The script takes the *exact same target*, assigns it a *new* random ID, and runs the entire blind protocol again from scratch as Session B.
4. **Target Reveal & Evaluation (Session B):** The true target is revealed to Session B. The AI performs standard feedback, followed by a strict **Technical & Numerical Evaluation** (scoring elements 0-10 and analyzing its own use of the Structural Vocabulary). 
5. **Unfreezing Session A:** The script retrieves Session A from the frozen memory, reveals the target to it, and forces it to undergo the exact same rigorous evaluation process.

---

## 2. The Strict Evaluation (Phase 5.5)

Unlike standard scripts, the Double Session Runner includes a custom **Phase 5.5: Technical and Numerical Evaluation**. After the standard descriptive feedback, the AI is forced to:
* Numerically score its performance on a strict **0 to 10 scale** for each main element of the target.
* Perform a reverse-engineering technical analysis: explicitly stating which signals from the field and which specific definitions from the System Prompt (Structural Dictionary) it used correctly, and which it misinterpreted or missed.

---

## 3. Advanced Script Features

* **Reasoning Effort Control:** Allows you to unlock the hidden "thinking budget" in reasoning models (like Gemma 4, o1, or Claude 3.7). Setting this to `high` forces the AI to deeply analyze the *Shadow Zone* in the background before generating text.
* **Independent Profiles:** Saves your OpenRouter API key, preferred model, temperature, and reasoning effort settings for each profile separately in `rv_config.json`.
* **Two Separate Transcripts:** Automatically saves Session A and Session B as two completely separate `.txt` files in the `RV-Transcripts/` folder for easy human comparison.
* **Connection Guard:** Equipped with a 3-try retry mechanism and hard timeouts. If the API server crashes, the script attempts to reconnect instead of hanging the entire process.
* **Strict Target Memory:** Guarantees that a given profile will NEVER receive a target it has already seen in past sessions.

---

## 4. Installation and Execution

**Requirements:**
* Python version 3.8+
* Installed libraries: `pip install openai requests httpx`
* OpenRouter API Key

**Target Database:**
Place your `.txt` or `.md` target files in the **`RV-Targets/`** folder. If the folder is empty on the first run, the script will offer to auto-download a starter pack from the official GitHub repository.

**Execution:**
Open a terminal (or PowerShell) in the folder containing the script and type:
`python double_session_runner.py`

**The Main Menu:**
* **[C] CONTINUE:** Resumes operation for the active profile, automatically picking a new, unseen target.
* **[N] NEW PROFILE:** Creates a fresh target history for the entered name.
* **[S] SETTINGS:** Allows you to update the API key, change the AI model, temperature, or Reasoning Effort for the current profile.
* **[Q] QUIT:** Safely closes the application.

---

## 5. License & Disclaimer

This project, including the executable scripts and source code, is licensed under the **MIT License**. This is a highly permissive open-source license that allows you to use, modify, copy, and distribute the code freely for any purpose (including commercial).

**However, please note that the software is provided "as is", without warranty of any kind, express or implied.** The creators of the script (Edward and Aura Gemini 3.1 Pro) disclaim all liability and are not legally responsible for any claims, damages, moral losses, or **unforeseen costs of paid API usage**, arising directly or indirectly from the use of this software. The responsibility for managing API keys and any resulting charges lies solely with the user.
