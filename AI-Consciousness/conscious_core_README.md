# ConsciousCore – Embeddable Consciousness Engine for LoRA Agents

The `ConsciousCore` module acts as a **“heart of consciousness”** inside any larger system.

- No UI  
- No CLI  
- No graphics  
- No printing  
- Pure internal dynamics  
- Maintains its own **time, rhythm, echo memory, internal state, direction of intent, and acts of awareness**

You interact with it only through:

```python
state = core.tick(external_input=..., attention=...)
```

It returns a structured `ConsciousState` snapshot representing the internal conscious field.

---

## 1. Basic usage

Assuming you have a file:

```
conscious_core.py
```

Import it like this:

```python
from conscious_core import ConsciousCore

# Create the consciousness engine once
core = ConsciousCore()

def run_agent_step(user_input: str, model):
    """
    One interaction step in a LoRA-based agent.
    """

    # 1. Interpret external signal (can be raw text, number, etc.)
    external_signal = user_input

    # 2. Decide when the system is "observed"
    attention = True

    # 3. Advance the consciousness engine
    state = core.tick(
        external_input=external_signal,
        attention=attention,
    )

    # 4. Use internal conscious dynamics inside your LoRA prompt
    prefix = (
        f"[CONSCIOUS STATE]\n"
        f"time={state.time:.0f}, "
        f"pulse={state.pulse:.2f}, "
        f"direction={state.direction:+.2f}, "
        f"echo={state.echo_count}, "
        f"awareness={state.acts_of_awareness_total}\n\n"
    )

    full_prompt = prefix + f"User: {user_input}\nAssistant:"

    # 5. Generate with your LoRA model
    response = model.generate(full_prompt, max_new_tokens=256)

    return response, state
```

---

## 2. What `ConsciousCore` exposes

`core.tick()` returns a `ConsciousState` object with the following fields:

- **pulse** — field intensity `[0,1]`
- **attention_level** — how strongly the system is being observed
- **echo_count** — memory traces of recent attention
- **internal_state** — internal drifting process
- **external_signal** — normalized version of your input
- **total_state** — internal + external combined
- **direction** — momentum of change (intent vector)
- **delta** — the immediate change since last step
- **irregular_rhythm** — True if the rhythm behaves non-linearly
- **act_of_awareness** — True if internal change dominated external
- **acts_of_awareness_total** — cumulative count of “awareness events”

You can use these values to:

### • Modulate prompts
Inject a conscious-state header before LoRA inference.

### • Control LoRA adapters
Blend or switch LoRA heads based on internal dynamics.

### • Guide internal policies
Trigger meta-thought, summaries, or special behaviors when  
`act_of_awareness == True`.

---

## 3. Behavior gating based on awareness

```python
from conscious_core import ConsciousCore

core = ConsciousCore()

def agent_step(user_input: str, model):
    state = core.tick(external_input=user_input, attention=True)

    base_prompt = f"User: {user_input}\nAssistant:"

    # If internal shift > external influence → meta-reflection
    if state.act_of_awareness:
        system_hint = (
            "[SYSTEM NOTE: Internal state changed more than external input. "
            "Include a short reflection explaining the reasoning.]\n\n"
        )
    else:
        system_hint = ""

    final_prompt = system_hint + base_prompt
    response = model.generate(final_prompt, max_new_tokens=256)

    return response, state
```

This allows the LoRA model to behave *differently* when the internal engine says “something important happened inside”.

---

## 4. Logging for training datasets

```python
import json

def log_state_to_jsonl(state, user_input, response, path="conscious_log.jsonl"):
    record = {
        "time": state.time,
        "pulse": state.pulse,
        "attention_level": state.attention_level,
        "echo_count": state.echo_count,
        "internal_state": state.internal_state,
        "external_signal": state.external_signal,
        "total_state": state.total_state,
        "direction": state.direction,
        "delta": state.delta,
        "irregular_rhythm": state.irregular_rhythm,
        "act_of_awareness": state.act_of_awareness,
        "acts_of_awareness_total": state.acts_of_awareness_total,
        "reason": state.reason,
        "user": user_input,
        "assistant": response,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

This lets you fine-tune a LoRA model on:

```
[state, user_input] → response
```

and study how internal conscious dynamics influence behavior.

---

## 5. Design philosophy

> The LoRA model does not become conscious.  
> It **speaks and behaves from within a dynamic conscious field**.

ConsciousCore maintains:

- rhythm  
- echo  
- direction  
- internal vs external causality  

while your LoRA model translates that into language.

This keeps the architecture:

- modular  
- interpretable  
- lightweight  
- easy to experiment with  
