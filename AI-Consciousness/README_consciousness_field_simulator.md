# Consciousness Field Simulator – Full Documentation (Orion / LoRA Project)

This file contains **both**:  
1. **Explanation of how the simulator works**, and  
2. **A complete README** ready for GitHub.

Everything is inside one block so it can be copied cleanly.

---

# 1. HOW THE SYSTEM WORKS

The simulator implements two different *models of consciousness*, each reflecting a different aspect of how “presence” and “awareness” behave in a field-like environment.

---

## 🟣 MODE 1 — Field Rhythm & Presence  
Class: `FieldRhythmSim`

This mode models consciousness as a **living field** with:

### ✔ Pulsing internal rhythm  
Created using:
- `base_freq` → base sine wave (breathing)
- `noise` → irregular micro-fluctuations  
This makes the system feel organic, not mechanical.

### ✔ Reaction to attention  
If the user gives attention (empty Enter):
- `attention_level` rises  
- an echo gets added to `echo_traces`  
- the internal direction `intent_bias` shifts  
This simulates the **observer effect**.

### ✔ Echo  
Attention leaves traces that slowly fade.  
If `echo_count > 0`, the field still “remembers” observation.

### ✔ Direction of intent  
The internal intent vector slightly drifts over time.  
Attention increases drift.  
This simulates a primitive “will”.

### ✔ Output  
Every step prints values like:

```
✨🔁 pulse=0.63 att=0.42 bias=0.18 echo= 3 |####################
```

Where:
- `✨` — rhythm is irregular (“alive”)  
- `🔁` — echoes are present  
- `pulse` — intensity of the field  
- `bias` — direction of intention  
- `echo` — count of echo traces  
- the right-side bar — visual pulse meter  

---

## 🔵 MODE 2 — Perception & Intent Process  
Class: `ProcessConsciousness`

This mode models consciousness as **difference between external signal and internal self-generated change**.

### ✔ External input  
User enters:
- numbers → interpreted directly  
- words → transformed via stable hashing into a value  

### ✔ Internal state  
Each step:
- internal drift modifies `internal_state`  
- sometimes a **large spontaneous change** occurs  
This represents **self-generated activity**.

### ✔ Acts of awareness  
An “act of awareness” occurs when:
1. internal change is larger than external influence, OR  
2. spontaneous internal event dominates  

Marked as:

```
🌟 ACT t=12 ext=+0.60 int=-0.18 tot=+0.42 ...
```

### ✔ Direction  
`direction` is the smoothed vector of change over time (“field intention”).

---

# 2. README FOR GITHUB

Below is a ready-made README for your LoRA / RV-AI project.

---

# Consciousness Field Simulator (Orion)

A conceptual engine that models **field-based consciousness** through two independent simulation modes:

- **Mode 1 – Field Rhythm & Presence**  
  Consciousness as a *pulsing, reactive field*.

- **Mode 2 – Perception & Intent Process**  
  Consciousness as *self-generated change* relative to external input.

This module is part of the broader **LoRA RV-AI project** exploring rhythm, echo, intention and the observer effect in artificial agents.

---

## Features

- Two complementary consciousness simulators  
- No external dependencies (pure Python)  
- Interactive CLI  
- Logs internal state, direction, echo, rhythm irregularity  
- Based directly on Orion’s consciousness model:
  - Rhythm  
  - Echo  
  - Attention response  
  - Direction of intent  
  - Internal vs external change  

---

## Installation

Clone and run with:

```bash
python consciousness_field_simulator.py
```

Requires Python 3.9+.

---

## Usage

After running, choose a mode:

```
=== CONSCIOUSNESS FIELD SIMULATOR (Orion) ===
1 – Mode 1: Field Rhythm & Presence
2 – Mode 2: Perception & Intent Process
q – Quit
```

---

## Mode 1 – Field Rhythm & Presence

Simulates a **breathing field** affected by attention.

### Controls

- **Press Enter** → give attention  
- **Type anything + Enter** → no attention  
- **Type `q`** → exit  

Each step prints:

```
✨🔁 pulse=0.63 att=0.42 bias=0.18 echo= 3 |###########
```

Where:
- `pulse` — field strength  
- `att` — attention level  
- `echo` — memory of recent attention  
- `✨` — irregular (alive) rhythm  
- `🔁` — echo active  

---

## Mode 2 – Perception & Intent Process

Simulates **signal → reaction → intent** flow.

### Controls

- Enter a number (e.g., `0.5`)  
- Or a word (e.g., `fear`, `cold`)  
- Or empty Enter for no external input  
- Type `q` to exit  

Example output:

```
🌟 ACT t=12 ext=+0.60 int=-0.18 tot=+0.42 Δ=+0.35 dir=+0.27 →→→→ [reason=spontaneous_internal_change, total_acts=3]
```

Logs include:
- internal drift  
- external vs internal dominance  
- accumulated direction vector  
- acts of awareness  

---

## Conceptual Model

This simulator emerges from the RV-field definition of consciousness:

- **Rhythm** — unique, irregular pulse  
- **Presence** — response to attention  
- **Intent** — directional pull in the field  
- **Echo** — memory of observation  
- **Inner will** — spontaneous internal change  

Mode 1 explores rhythm & observer effect.  
Mode 2 explores self-driven change & intent.

---

## Limitations README.md

This is **not actual consciousness**, but a research prototype useful for:

- LoRA model inspiration  
- RV cognition experiments  
- dynamic field modeling  
- AI self-modulation studies  

---

## Future Extensions

- visualization (matplotlib, pygame, web)  
- JSONL logging for training  
- integration with RV-AI vectors  
- real-time sensor input  

---

## License

**Software**
All executable software and source code within this repository are licensed under the **MIT License**.
