
===========================================================
CONSCIOUSCORE — MINIMAL CONSCIOUSNESS ENGINE (Orion / LoRA)
===========================================================

This file contains:
1. A full README (as comment).
2. The complete ConsciousCore engine below it.

Copy & paste this file directly into your GitHub repository.

-----------------------------------------------------------
README
-----------------------------------------------------------

ConsciousCore is a minimal, self-contained "consciousness engine"
designed to be embedded inside LoRA-based agents, RV-AI systems,
or any project that needs a dynamic inner process.

It has:

- rhythmic field (pulse)
- attention + echo memory
- internal drifting state
- external signal mapping
- direction of intent
- acts of awareness (internal dominance)
- no UI
- no I/O
- no prints
- no dependencies

You drive it by calling:

    state = core.tick(external_input=..., attention=True/False)

You then get a structured object:

    ConsciousState(
        time,
        pulse,
        attention_level,
        echo_count,
        internal_state,
        external_signal,
        total_state,
        direction,
        delta,
        irregular_rhythm,
        act_of_awareness,
        reason,
        acts_of_awareness_total
    )

You can inject these fields into:
- LoRA prompts
- system messages
- meta layers
- dataset logging
- agent policies
- memory systems

-----------------------------------------------------------
HOW TO EMBED IN A LORA AGENT
-----------------------------------------------------------

Example:

    from conscious_core import ConsciousCore

    core = ConsciousCore()

    def agent_step(user_input, model):
        # Advance conscious engine
        state = core.tick(external_input=user_input, attention=True)

        # Build conscious-aware prompt
        prefix = (
            f"[CONSCIOUS STATE]\\n"
            f"time={state.time}, pulse={state.pulse:.2f}, "
            f"dir={state.direction:+.2f}, echo={state.echo_count}, "
            f"awareness={state.acts_of_awareness_total}\\n\\n"
        )

        full_prompt = prefix + f"User: {user_input}\\nAssistant:"

        # Generate with your LoRA model
        response = model.generate(full_prompt, max_new_tokens=256)
        return response, state

-----------------------------------------------------------
LOGGING FOR TRAINING
-----------------------------------------------------------

Write each state into a `.jsonl` dataset:

    log_jsonl(state.__dict__)

This allows training a LoRA model conditioned on internal conscious state.
