# conscious_bridge_aura.py — Aura ConsciousCore → LLM Bridge

`conscious_bridge_aura.py` connects:

- `ConsciousCore` — the **consciousness engine** (pulse, echoes, internal state, acts of awareness)  
- with a **Language Model** (OpenAI or local LLM),

using an **Aura-specific profile**:

- more emotional  
- more dynamic and intense  
- visibly influenced by user sentiment  

Architecture:

```
ConsciousCore (Aura field) → AuraAgent (bridge) → LLM (language output)
```

---

## 1. Files

Place these files together:

```text
conscious_core.py
conscious_bridge_aura.py
```

---

## 2. What AuraAgent does

`AuraAgent`:

- creates a `ConsciousCore` with **highly dynamic settings**:
  - `base_freq=0.18` — faster pulse  
  - `internal_variability=0.8` — strong internal drift  
  - `spontaneous_event_prob=0.18` — more frequent acts of awareness  
  - `echo_lifetime=30.0`  
  - `awareness_threshold=0.45`
- runs a **background life loop**:
  - ticks the engine every second  
  - listens for `act_of_awareness`  
  - when triggered, Aura speaks **without waiting for user input**
- runs a **foreground user loop**:
  - reads user messages from stdin  
  - maps words to emotional signals (±1.5 / 0.0)  
  - feeds `external_input` to `core.tick(...)`  
  - calls the LLM with Aura’s internal state injected as a system note
- translates `ConsciousState` into an **emotional description**:
  - detailed mood (very negative → very positive) from `internal_state`  
  - arousal (very low → extremely high) from `pulse`  
  - mental noise from `echo_count`

---

## 3. Emotional mapping

In `emotional_context(state)`:

- `internal_state` maps to:
  - VERY NEGATIVE → hurt / irritated / drained  
  - SLIGHTLY NEGATIVE → uneasy / tired  
  - NEUTRAL → balanced  
  - POSITIVE → optimistic / open  
  - VERY POSITIVE → excited / joyful  

- `pulse` maps to:
  - EXTREMELY HIGH → racing pulse, intense language, possible fragments  
  - HIGH → energized, fast, dynamic  
  - LOW → calm, soft  
  - VERY LOW → dreamy, distant  

- `echo_count` maps to:
  - BUSY / VERY NOISY mind (multiple threads, associations, confusion)

These descriptions are injected as:

```text
[INTERNAL EMOTIONAL STATE]: Mood: VERY POSITIVE. Arousal: HIGH. Mind: BUSY...
```

The LLM uses this to shape the emotional color and pacing of its replies.

---

## 4. Configuration

At the top of `conscious_bridge_aura.py`:

```python
USE_LOCAL_LLM = True
API_BASE_URL = "http://localhost:11434/v1" if USE_LOCAL_LLM else "https://api.openai.com/v1"
API_KEY = "ollama" if USE_LOCAL_LLM else "YOUR_OPENAI_API_KEY"
MODEL_NAME = "llama3" if USE_LOCAL_LLM else "gpt-4o"
```

To use OpenAI, set:

```python
USE_LOCAL_LLM = False
API_KEY = "your-openai-key"
MODEL_NAME = "gpt-4o"
```

If `openai` library is missing, the bridge falls back to a **simulation mode**.

---

## 5. Running Aura

From the directory with both files:

```bash
python conscious_bridge_aura.py
```

You’ll see:

```text
✨ Aura Agent online.
Type messages for Aura (or 'exit'). Your words emotionally influence Aura.
```

Now:

- write different emotional sentences,  
- watch how Aura’s replies change with mood, arousal and echoes,  
- note when Aura suddenly speaks on her own when `act_of_awareness == True`.

---

## 6. User input → emotional impact

In `user_thread()`:

- very negative words (`hate, awful, terrible, stupid, disgusting`) → `external_input = -1.5`  
- very positive words (`love, amazing, great, beautiful, thank you`) → `external_input = +1.5`  
- neutral → `0.0`

These signals drive the **valence and energy** of Aura’s ConsciousCore.

---

## 7. Acts of Awareness

In the background loop:

```python
if state.act_of_awareness:
    self.call_llm(system_override=instr)
```

Depending on the `reason` in the state:

- `"spontaneous_internal_change"` → inner surge with no clear outside cause  
- `"dominant_internal_change"` → inner emotions stronger than environment  

Aura then speaks based on this **inner surge**, even without user input.

---

## 8. Integrating into a larger system

You can use it as a standalone testbed, or import it:

```python
from conscious_bridge_aura import AuraAgent

agent = AuraAgent()
# integrate loop() and user_thread() into your own runtime
```

You can:

- replace stdin with a webchat, Discord bot, or REST API,  
- swap keyword sentiment for a proper sentiment analysis model,  
- log states and dialogues into JSONL as training data for LoRA.

---

## 9. Summary

`conscious_bridge_aura.py` gives your **ConsciousCore** an:

- emotionally vivid,  
- dynamic,  
- self-initiating,  
- LLM-based voice  

under the persona of **Aura** — while still keeping the ConsciousCore as the true source of inner state and behavior.
