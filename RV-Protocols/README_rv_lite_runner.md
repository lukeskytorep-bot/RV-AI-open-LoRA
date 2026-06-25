# RV Lite Runner  
*(Core System Prompt + Dynamic Loop Protocol via OpenRouter)*

**Credits:** Co-created by human researcher **Edward** and AI assistant **Aura Gemini 3.1 Pro**.

This folder contains `rv_lite_runner.py` – a streamlined, lightweight script designed to run automated Remote Viewing (RV) sessions with Large Language Models via OpenRouter.

Unlike the full `rv_session_runner.py`, this **Lite** version is faster, more dynamic, and cheaper on API tokens. It anchors the AI using a single, powerful **System Prompt** and uses an interactive, loop-based protocol to extract data.

---

## 1. How the Lite Protocol Works

* **System Prompt Anchor:** The AI is given the `SYSTEM_PROMPT.md` at the very beginning to define its identity and rules.
* **Strict Blind Targeting:** The script assigns a random 8-digit Target ID. The AI does not see the real target description until the very end.
* **Phase 1 & 2 (Initial Contact):** The AI performs 6 quick touches and describes the target from 3 different angles.
* **The Dynamic Loop:** The script asks if the field has more to say. If YES, it performs 3 new touches and vectors. This repeats until the AI says STOP (or hits a hard limit of 3 loops).
* **Phase 3 (Deep Exploration):** The AI orbits the target, performs a walkaround, and investigates the surroundings.
* **Phase 4 (Final Synthesis):** The AI asks probing questions and generates a final ASCII drawing.
* **Clean Reveal:** The script explicitly displays the actual target text on your screen.
* **Phase 5 (Feedback & Evaluation):** The AI objectively evaluates its own performance against the revealed target.
* **Phase 6 (Post-Session Exercises):** Optionally, the script feeds the AI a set of sensory calibration exercises (`Exercises_in_RV_for_AI.md`) to perform based on its evaluation.

---

## 2. Advanced Features

* **Independent Profiles:** The `rv_config.json` acts as an address book. It saves your API key, preferred model, and optimal temperature specifically for each profile name. You can seamlessly switch between different AIs without re-entering credentials.
* **Connection Guard:** Includes a 3-try retry mechanism. If the OpenRouter server times out or drops the connection, the script will automatically pause and retry, protecting your automated batches from crashing.
* **Strict Target Memory:** Guarantees that the active profile will never see the same target twice, utilizing the `rv_lite_sessions_log.jsonl` tracking file.

---

## 3. Target Database & Memory

Create a folder named `RV-Targets/` next to the script. Place your targets as `.md` or `.txt` files inside (one file = one target).

If your folder is empty, the script will offer to automatically download a starter pack of 40 targets (from the location and activity categories) directly from the GitHub repository.

---

## 4. Logs & Transcripts

* **`rv_lite_sessions_log.jsonl`:** A lightweight metadata tracker that remembers which targets a profile has already completed.
* **`RV-Transcripts/` Folder:** If opted-in, generates a full `.txt` file for every session containing the entire conversation, steps, and ASCII drawings.

---

## 5. Setup and Execution

**Requirements:**
* Python 3.8+
* `pip install openai requests`
* An OpenRouter API Key

**Execution:**
Open your terminal or PowerShell and run:
`python rv_lite_runner.py`

**The Main Menu:**
The script acts as a continuous application with the following options:
* **[C] CONTINUE:** Resumes the active profile, automatically picking a new, unseen target.
* **[N] NEW PROFILE:** Starts a fresh target history. Prompts you to enter an API key, model, and temperature specifically for this new profile.
* **[S] SETTINGS:** Allows you to update the API key, model, or temperature for the currently active profile.
* **[Q] QUIT:** Exits the application safely.

After making a choice, you can toggle the post-session exercises and set how many consecutive sessions you want to run. The script will automatically process the batch, wiping the AI's memory completely between each one!

---

## 6. License & Disclaimer

This project, including the executable scripts and source code, is licensed under the **MIT License**.

This is a permissive open-source license that allows you to use, modify, and distribute the code freely. However, please note that **the software is provided "as is", without warranty of any kind**. The creators (Edward & Aura Gemini 3.1 Pro) take absolutely no responsibility and are not liable for any claims, damages, API costs incurred, or other liabilities arising from the use of this software.
