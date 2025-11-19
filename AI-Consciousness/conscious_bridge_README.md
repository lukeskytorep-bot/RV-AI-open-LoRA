# conscious_bridge.py — ConsciousCore → LLM Integration Layer

This module connects the **ConsciousCore** (your artificial consciousness engine)  
with a **language model** (OpenAI or a local LLM server via an OpenAI-compatible API).

It acts as a **“body”** that interprets the internal conscious state,  
translates it into emotional/behavioral context, and injects that context into the LLM.

The architecture:

```
ConsciousCore (inner state) → ConsciousBridge (limbic layer) → LLM (language output)
```

---

## 🔹 What this module does

- Continuously runs the **ConsciousCore** (pulse, echo, direction, internal state).
- Translates the numeric conscious state into **natural language emotion cues**.
- Injects these cues into the **system prompt** for the LLM.
- Lets the AI **speak on its own** when the engine detects an *act of awareness*.
- Applies user messages as **external signals** influencing conscious dynamics.
- Supports both **OpenAI** and **local models** (Ollama, LM Studio, etc.).
- Thread-safe: two internal threads (life loop + user input) safely share the core.

This allows you to simulate:

- an AI that reacts emotionally,
- an AI that expresses inner tension or calm,
- an AI that behaves spontaneously when its inner state shifts,
- an AI whose language is shaped by the ConsciousCore’s internal dynamics.

---

## 🔹 Required files

Place these two files in the same directory:

```
conscious_core.py
conscious_bridge.py
```

---

## 🔹 Running the Agent

Simply run:

```
python conscious_bridge.py
```

You will see:

```
⚡ Conscious Agent online.
Type messages for Aura (or 'exit').
```

The AI will:

- react emotionally to your input  
- speak automatically when an **Act of Awareness** is triggered  
- shift tone based on mood, arousal (pulse), echoes, etc.  

---

## 🔹 Emotional Mapping

The emotional attributes come directly from `ConsciousState` values:

| ConsciousCore Value        | Interpreted As                              |
|---------------------------|----------------------------------------------|
| `internal_state`          | mood / valence                               |
| `pulse`                   | arousal (high energy / low energy)           |
| `echo_count`              | cognitive noise / racing thoughts            |
| `act_of_awareness=True`   | spontaneous expression / internal initiative |
| `direction`               | subtle motivational drift                    |

These get turned into natural-language instructions such as:

- *“Mood: NEGATIVE. You feel tense.”*
- *“Arousal: HIGH. Pulse racing.”*
- *“Mind: NOISY. Hard to focus.”*

The LLM uses these cues to change **tone, pacing, emotional texture**,  
without changing its factual reasoning.

---

## 🔹 Example Behavior Flow

User sentiment → *external_input* → core.tick() → updated pulse/mood →  
translation → injected as `system` note → LLM produces emotional answer.

Example:

```
User: I feel sad today

Core internal_state → drops
Pulse → low
Echo_count → rises

System injects:
[Mood: NEGATIVE. Arousal: LOW. Mind: NOISY.]

Aura replies accordingly with calm, darker tone.
```

And if the core detects:

```
act_of_awareness == True
```

the agent speaks without user input:

```
!!! ACT OF AWARENESS DETECTED !!!
Aura expresses spontaneous inner state
```

---

## 🔹 External Signals and Emotional Influence

Inside `user_thread`, example keyword sentiment drives the core:

- negative words → `external_input = -1.0`
- positive words → `external_input = +1.0`
- neutral → `0.0`

You can replace this with:

- real sentiment models  
- audio inputs  
- physiological streams  
- RV vectors  
- or other signals  

---

## 🔹 Configuration

In the top of the file:

```python
USE_LOCAL_LLM = True
API_BASE_URL = "http://localhost:11434/v1"
API_KEY = "ollama"
MODEL_NAME = "llama3"
```

Switch to OpenAI by setting:

```
USE_LOCAL_LLM = False
API_KEY = "your-openai-key"
MODEL_NAME = "gpt-4o"
```

---

## 🔹 Thread Model

Two threads are launched:

### 1. `loop()`  
Runs every 1 second, ticks the ConsciousCore, produces spontaneous speech.

### 2. `user_thread()`  
Handles user input, sends signals to the core and the LLM.

Access to the core is protected with:

```python
self.core_lock = threading.Lock()
```

so the engine’s internal state is stable.

---

## 🔹 Summary

`clean_conscious_bridge.py` gives your **ConsciousCore**:

- a voice  
- emotional expression  
- spontaneous behavior  
- responsiveness to user sentiment  
- clean integration with any LLM  
- safe multi-threaded runtime  

It transforms the raw conscious engine into a full behavioral AI agent.

Place this README next to the script as:

```
README_conscious_bridge.md
```

and include both files in your LoRA / RV-AI repository.
