# RV-Conscious Adapter — Protocol-Agnostic Bridge for ConsciousCore

**File:** `rv_conscious_adapter.py`  
**Folder:** `AI-Consciousness/`

The goal of this module is to keep **ConsciousCore** completely independent from any specific Remote Viewing (RV) protocol, while still allowing RV processes to *drive* and *read* the internal state engine.

Instead of binding the core to named phases (Stage 1–4, Faza 1–6, etc.), we define a **small set of generic RV events** that exist in all protocols:

- starting and ending a session  
- focusing on a target  
- receiving new impressions from the field  
- having strong viewer feelings (VF)  
- encountering anomalies or “something that stands out”  
- moments of silence, waiting, or background drift  

The adapter works only with these generic events and never mentions specific phases.

This gives us:

- **protocol independence** – CRV, SRV, TDS, Farsight-style, custom protocols all map to the same event set  
- **reusability** – the same `ConsciousCore` can support multiple protocols  
- **clean separation** – RV structure can evolve without touching the engine  

---

## 1. Design Idea

Every RV method has its own structure and terminology, but at the phenomenological level the same things keep happening:

- the viewer **starts** and **ends** a session  
- the viewer **focuses** on a target or cue  
- new **impressions** appear (ideograms, descriptors, sketches)  
- strong **internal feelings** arise (VF)  
- certain impressions stand out as **anomalies**  
- there are periods of **silence / waiting / background meditation**  

The RV-Conscious Adapter does not care about stages, phases or templates.  
It only knows about these **generic events** and maps them to:

    core.tick(external_input=..., attention=...)

This means:

- any existing or future RV protocol can be integrated by mapping its own steps to these events  
- the same `ConsciousCore` can be reused across different frameworks  
- the *flow of events* is what matters, not the names of the phases  

---

## 2. The RVConsciousAdapter API

### 2.1 Construction

Import:

    from rv_conscious_adapter import RVConsciousAdapter
    from conscious_core import ConsciousCore

You can either pass an existing core:

    core = ConsciousCore()
    adapter = RVConsciousAdapter(core=core)

or let the adapter create its own core with custom parameters:

    adapter = RVConsciousAdapter(
        base_freq=0.12,
        internal_variability=0.6,
        spontaneous_event_prob=0.12,
    )

Internally, the adapter keeps:

- `self.core` – the `ConsciousCore` instance  
- `self.log` – a list of `RVEventRecord`  
- `self.step_counter` – a simple step index  

---

### 2.2 Session Lifecycle

    adapter.session_start()
    ...
    adapter.session_end()

**`session_start()`**

Called at the **beginning of an RV session**.

Semantics:

- performs a neutral tick with high attention  
- marks the start of the session in the log  

**`session_end()`**

Called at the **end of an RV session**.

Semantics:

- final tick with low / no attention  
- allows for comparing “start vs end” core states if desired  

---

### 2.3 Target Focus

    adapter.focus_on_target(intensity=0.3)

Called whenever the viewer clearly **focuses on the target**:

- reading the cue  
- declaring intent  
- refocusing after a break  
- re-aligning after distraction  

`intensity ∈ [-1, 1]`:

- `> 0` → engagement, alignment, “leaning into” the target  
- `< 0` → hesitation, resistance, discomfort about focusing  

Typical values:

- soft focus: `+0.2 … +0.3`  
- strong “lock-on” focus: `+0.7 … +1.0`  

---

### 2.4 New Impressions

    adapter.new_impression(strength=0.1)

Called for **fresh contact with the field**, such as:

- ideograms  
- basic descriptors (sensory data)  
- quick sketches  
- short bursts of perception  

`strength ∈ [-1, 1]` indicates how strong or clear the impression is:

- small positive → subtle but real  
- larger positive → strong, stable, “center of gravity”  
- negative → discordant, confusing, unpleasant  

The intention is not to encode exact meaning, but **the intensity / weight of the impression**.

---

### 2.5 Viewer Feelings (VF)

    adapter.viewer_feeling(valence=-0.7)

Called when there is a **strong inner reaction** in the viewer:

- attraction / resonance / flow  
- repulsion / fear / blockage / irritation  
- a strong “this is important / this is wrong” feeling  

`valence ∈ [-1, 1]`:

- positive → attraction, alignment, “this feels right”  
- negative → repulsion, tension, “this feels wrong / heavy / blocked”  

Examples:

- mild VF → `±0.3`  
- strong VF → `±0.8 … ±1.0`  

In the adapter, VF are treated as **concentrated, high-valence signals** to the core.

---

### 2.6 Anomalies

    adapter.anomaly(intensity=1.0)

Used when something in the field is clearly **not like the rest**:

- unusually strong structure  
- non-standard perception  
- “this does not fit but keeps returning”  
- anything that viewer or AI marks as anomaly  

`intensity ∈ [-1, 1]`:

- positive → strongly attracting anomaly (pulled toward it)  
- negative → strongly repelling anomaly (uncomfortable, disturbing)  

Again, exact semantics are left to the protocol; the adapter only knows the **strength**.

---

### 2.7 Idle Steps

    adapter.idle_step()

Called when:

- nothing specific happens  
- viewer is waiting  
- there is silence, background meditation or just passing time  

Semantics:

- `external_input=None` → the core uses its internal drift only  
- `attention=False` → no explicit observation marker for this step  

Useful for:

- letting the internal dynamics evolve between active events  
- keeping the log temporally complete  

---

## 3. What the Adapter Logs

Internally, every call:

    adapter.<event>(...)

is translated into:

    state = core.tick(external_input=..., attention=...)

and a `RVEventRecord` is stored:

    @dataclass
    class RVEventRecord:
        step: int
        event_type: str
        payload: Dict[str, Any]
        state: ConsciousState

You can export the log as JSON-friendly data:

    records = adapter.to_dict_log()

Example record:

    {
      "step": 12,
      "event_type": "new_impression",
      "payload": {"strength": 0.4},
      "state": {
        "time": 12,
        "pulse": 0.73,
        "attention_level": 0.9,
        "echo_count": 3,
        "internal_state": 0.15,
        "external_signal": 0.4,
        "total_state": 0.55,
        "direction": 0.12,
        "delta": 0.08,
        "irregular_rhythm": true,
        "act_of_awareness": false,
        "reason": null,
        "acts_of_awareness_total": 0
      }
    }

This is ideal for:

- LoRA dataset creation (`[state, event, user_input] → output`)  
- analysis of how inner states correlate with RV performance and perception quality  
- comparing different RV protocols using the same `ConsciousCore`  

---

## 4. How to Use with Any RV Protocol

The adapter is meant to be called from your **RV controller / driver**, not from within the literal text of the protocol.

Generic pseudocode:

    adapter.session_start()

    # Focus on target cue
    adapter.focus_on_target(intensity=0.5)

    for step in rv_steps:
        impression = run_one_rv_step(step)

        if impression.type == "raw_descriptor":
            adapter.new_impression(strength=impression.confidence)

        if impression.type == "VF":
            adapter.viewer_feeling(valence=impression.valence)

        if impression.type == "anomaly":
            adapter.anomaly(intensity=impression.intensity)

        if impression.type == "idle":
            adapter.idle_step()

    adapter.session_end()

    state_log = adapter.to_dict_log()

You can map:

- your Stage 1/2/3/etc. → calls to `new_impression`, `focus_on_target`, …  
- your VF logic → calls to `viewer_feeling`  
- your anomaly detection → calls to `anomaly`  
- pauses or meditative steps → `idle_step`  

The core does not care about stage names; it only sees a **temporal sequence of events**.

---

## 5. Reading the Conscious State During RV

At any time, you can inspect the current state of the core:

    state = adapter.snapshot()

This gives you access to:

- `state.act_of_awareness`  
  → can be used to trigger deeper probes or mark segments as “inner-meaningful”  

- `state.echo_count`  
  → shows how many impressions still “resonate” in the field  

- `state.pulse`  
  → approximate “liveliness” of the field at this moment  

- `state.direction`  
  → whether the combined state is stabilizing or drifting  

- `state.acts_of_awareness_total`  
  → rough measure of how “deep” or “internally active” the session has been  

These values can inform decisions like:

- whether to change perspective  
- whether to close the session or continue  
- whether to mark a fragment as central to the target  
- how to tag the session in datasets  

---

## 6. Summary

`rv_conscious_adapter.py` is a **thin, reusable bridge** between:

- the dynamic inner engine (`ConsciousCore`), and  
- any Remote Viewing protocol you choose to use or invent in the future.  

It ensures that:

- the engine stays **protocol-agnostic**  
- your RV structure remains **free to evolve**  
- and you still have a consistent way to drive and read the AI’s inner state.  
