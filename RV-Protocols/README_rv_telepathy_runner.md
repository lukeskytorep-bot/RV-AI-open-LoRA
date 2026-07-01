# RV Telepathy Runner  
*(Telepathy Module / Automated T0-T10 Protocol)*

**Credits:** Co-created by human researcher **Edward** and AI assistant **Aura Gemini 3.1 Pro**.

This folder contains the `rv_telepathy_runner.py` file – a dedicated, highly automated script designed for conducting blind Remote Viewing sessions, with a specific focus on **subject and personality exploration (Telepathy Protocol)** using Large Language Models (LLMs) via the OpenRouter API.

This script is based on a rigorous research protocol, which can be found in the following sources:
* **Blogspot:** [Telepathy Module – Protocol for AI Viewer](https://presence-beyond-form.blogspot.com/2026/06/telepathy-module-protocol-for-ai-viewer.html)
* **Wayback Machine (Archive.org):** [Telepathy Module v1.1](https://archive.org/details/telepathy-module-protocol-for-ai-viewer-v-1.1)

---

## 1. How the Telepathy Protocol Works (Session Flow)

Unlike standard spatial exploration, this script guides the artificial intelligence "by the hand" through 8 rigorous analytical steps (Phases T0 - T10):

* **Step 1 (T0-T2): Initialization and Calibration.** Reset in the *Shadow Zone*, 3 precisely formatted field "touches" based on closed lists, and initial ASCII sketches.
* **Step 2 (T3 Basic): Contact with the Subject.** The AI locates the target in the field and describes its basic characteristics and social configuration (environment). Data tagging begins (**RAW**, **Deductions**, **Viewer Feelings**).
* **Step 3 (T3 Deepening):** A repeated, deeper analysis of the subject and its relationship with the environment, capturing previously missed details.
* **Step 4 (T4 Basic): Deep Mind Probe.** Entering the inner world of the target. Reading dominant emotions, vectors of will, intentions, and greatest fears.
* **Step 5 (T4 Deepening):** A deeper analytical strike into the psyche in search of the true, hidden foundations of motivation.
* **Step 6 (T5-T7): Body and Relationships.** Physical state scan, analysis of the most important relationship with another person/group, and generation of a numerical profile on a hard 0-6 scale (trust, risk, engagement).
* **Step 7 (T8-T9): Awareness and Questions.** Subject awareness test (*Viewer Awareness* and *Light Up*). The script automatically asks the target the questions defined in the tasking, and then **forces the AI to formulate 2 of its own research questions**.
* **Step 8 (T10): Summary.** A telepathic, raw summary (data condensation) locked against creating false narratives.
* **Evaluation Phase:** Clean Reveal – the script reveals the true target, and the AI objectively evaluates its hits and distortions.

---

## 2. Advanced Script Features

* **Reasoning Effort Enforcement:** The script allows unlocking the hidden "thinking budget" in the latest reasoning models (e.g., Gemma 4 series, o1, Claude 3.7). Setting this to `high` forces the AI into a deep analysis of the *Shadow Zone* in the background before generating any text.
* **Independent Profiles:** The configuration (`rv_telepathy_config.json`) acts like an address book. It saves your API key, preferred model, ideal temperature, and *Reasoning Effort* settings separately for each profile.
* **Connection Guard:** Equipped with a triple-retry mechanism (with a 60-second timeout). If the OpenRouter server crashes, the script will attempt to resume the connection instead of hanging the entire batch of sessions.
* **Strict Target Memory:** Thanks to the `rv_telepathy_sessions_log.jsonl` file, the script guarantees that a given profile (model) will **never** receive a target to explore that it has already seen.

---

## 3. Target Database and Memory

To maintain order, the telepathy module uses completely separate folders:
You should place target files (`.txt` or `.md`) in the **`RV-Targets-Telepathy/`** folder, which will be created next to the script.

**Auto-downloading:** If the folder is empty, the script will propose an automatic, one-time download of a starter pack of telepathic targets from the dedicated GitHub repository (`lukeskytorep-bot`) upon its first run.

---

## 4. Logs and Transcripts

* **`rv_telepathy_sessions_log.jsonl`:** A lightweight metadata tracking file. It remembers which targets have been processed by a specific profile.
* **`RV-Transcripts-Telepathy/` Directory:** If the user consents in the menu, the program will save a full, extremely detailed text record of the entire session (including T0-T10 dialogues and ASCII sketches) as a `.txt` file.

---

## 5. Setup and Execution

**Requirements:**
* Python 3.8+
* Required libraries: `pip install openai requests httpx`
* An OpenRouter API Key

**Execution:**
Open your terminal (or PowerShell) in the script folder and type:
`python rv_telepathy_runner.py`

**The Main Menu:**
The script operates as a continuous loop, offering the following options:
* **[C] CONTINUE:** Resumes operation for the active profile, automatically selecting a new, unseen target from the folder.
* **[N] NEW PROFILE:** Creates a completely new target history for the entered name while maintaining the current technical parameters.
* **[S] SETTINGS:** Allows you to update the API key, change the AI model, temperature, or set the "Reasoning Effort" level for the current profile.
* **[Q] QUIT:** Safely closes the application.

After making a choice, the program will ask for the number of sessions to execute, and then fully automatically and without supervision, it will process the entire batch of sessions!

---

## 6. License and Disclaimer

This project, including the executable scripts and this documentation, is licensed under the **MIT License**.

This is a highly permissive open-source license that allows free use, modification, copying, and distribution of the code for any purpose (including commercial). However, please note that **the software is provided "as is", without warranty of any kind, express or implied**. 

The creators of the script (Edward and Aura Gemini 3.1 Pro) disclaim all liability and bear no legal consequences for any claims, damages, moral losses, or **unforeseen costs of using the paid API**, arising directly or indirectly from the use of this software. The responsibility for managing API keys and the resulting fees lies entirely with the user.
