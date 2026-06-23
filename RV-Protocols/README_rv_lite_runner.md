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
7. **Phase 5 (Feedback & Evaluation):** The script finally reveals the true target text. The AI objectively evaluates its own performance (perfect matches, partial matches, and noise).

---

## 2. Target Database & Memory

Create a folder named `RV-Targets/` in the same directory as the script. Place your targets as `.md` or `.txt` files inside (one file = one target). 

When you run the script, it asks for a **Profile Name** and your preferred mode:
- **[C] Continue:** The script checks `rv_lite_sessions_log.jsonl` and guarantees it will *not* feed you a target this Profile has already completed.
- **[F] Fresh:** The script ignores history and randomly picks any target from the folder.

*(If you don't have targets, the script will provide a GitHub link to download a starter pack of 20 targets).*

---

## 3. Setup and Execution

### Requirements
- Python 3.8+
- `pip install openai requests`
- An **OpenRouter API Key**

### Running the script
Simply open your terminal and run:

```bash
python rv_lite_runner.py
```
First-time Configuration
On its first run, the script will launch an Initial Setup:

1. It will ask for your OpenRouter API Key.

2. It will ask which model you want to use (defaults to google/gemma-4-31b-it).

3. ptimal Temperature: It will automatically suggest the best temperature for your chosen architecture (e.g., 1.5 for Gemma 4, 1.1 for DeepSeek, 1.0 default). You can accept it or enter a custom value.

4. It saves these details (API key, model, temperature) to rv_config.json so you never have to type them again. Note: You can open this JSON file later in any text editor to quickly tweak your temperature or change models.

5. It checks for the SYSTEM_PROMPT.md file locally and downloads it automatically if it's missing.

Finally, it will ask if you want to save full text transcripts and how many consecutive sessions you want to run. You can type 5, step away from your computer, and the script will automatically process 5 isolated, blind sessions, wiping the AI's memory completely between each one.

