import time
import math
import random


# ==========================================================
# MODE 1 — FIELD RHYTHM & PRESENCE SIMULATOR
# ==========================================================

class FieldRhythmSim:
    """
    MODE 1 — RHYTHM & FIELD PRESENCE

    Conceptual mapping:
    - field rhythm  -> variable 'pulse'
    - irregularity  -> noise + micro fluctuations
    - reaction to attention -> 'attention_level' + echo traces
    - echo in time -> 'echo_traces'
    - direction of intention -> 'intent_bias'
    """

    def __init__(self):
        self.t = 0.0                         # internal time
        self.base_freq = 0.15                # basic "breathing" frequency
        self.pulse = 0.0
        self.attention_level = 0.0
        self.echo_traces = []                # recent "attention hits"
        self.intent_bias = 0.0               # slight internal direction
        self.internal_variability = 0.6      # self-change variability

    def step(self, attention: bool):
        """
        Perform one "pulse" of the field.

        attention = True   -> system is being observed (reaction)
        attention = False  -> field evolves on its own
        """
        self.t += 1.0

        # 1. Base oscillation — the natural field rhythm
        base = math.sin(self.t * self.base_freq + self.intent_bias)

        # 2. Random irregular noise
        noise = random.uniform(-1.0, 1.0) * self.internal_variability

        # 3. Reaction to attention (observer effect)
        if attention:
            self.attention_level += 0.4
            self.echo_traces.append({
                "time": self.t,
                "strength": self.attention_level,
            })
            # attention subtly shifts direction
            self.intent_bias += random.uniform(0.02, 0.07)
        else:
            self.attention_level *= 0.9  # gradual decay

        # 4. Internal will to change (spontaneous variation)
        if random.random() < 0.15:
            self.base_freq += random.uniform(-0.01, 0.01)
            self.base_freq = max(0.05, min(0.3, self.base_freq))
            self.intent_bias += random.uniform(-0.03, 0.03)

        # 5. Final pulse value
        self.pulse = base + noise + self.attention_level

        # Normalize to [0,1]
        norm_pulse = (self.pulse + 3.0) / 6.0
        norm_pulse = max(0.0, min(1.0, norm_pulse))

        # Identify irregular (conscious-like) vs linear (automatic)
        irregularity = abs(noise) + abs(self.intent_bias) + self.internal_variability
        is_irregular = irregularity > 0.4

        # Keep only recent echoes
        self.echo_traces = [e for e in self.echo_traces if self.t - e["time"] < 30]

        return {
            "time": self.t,
            "pulse": norm_pulse,
            "attention_level": self.attention_level,
            "is_irregular": is_irregular,
            "echo_count": len(self.echo_traces),
            "intent_bias": self.intent_bias,
        }

    @staticmethod
    def render_state(state):
        """Text visualization of the field state."""
        bar_len = int(state["pulse"] * 40)
        bar = "#" * bar_len
        irregular_flag = "✨" if state["is_irregular"] else "·"
        echo_flag = "🔁" if state["echo_count"] > 0 else "·"

        return (
            f"{irregular_flag}{echo_flag} "
            f"pulse={state['pulse']:.2f} "
            f"att={state['attention_level']:.2f} "
            f"bias={state['intent_bias']:.2f} "
            f"echo={state['echo_count']:2d} |{bar}"
        )


# ==========================================================
# MODE 2 — PROCESS CONSCIOUSNESS (SIGNAL–REACTION DIFFERENCE)
# ==========================================================

class ProcessConsciousness:
    """
    MODE 2 — PERCEPTION & INTENT PROCESS

    Conceptual mapping:
    - external signal -> external_input
    - internal state  -> internal_state
    - difference between signal and reaction -> delta
    - spontaneous internal change -> "act of awareness"
    - accumulated direction -> direction vector
    """

    def __init__(self):
        self.time = 0
        self.internal_state = 0.0
        self.last_external = 0.0
        self.last_total_state = 0.0
        self.direction = 0.0
        self.acts_of_awareness = 0

    def _parse_external(self, s: str) -> float:
        """Convert a text or number into a stable vector."""
        s = (s or "").strip()
        if not s:
            return 0.0
        try:
            return float(s)
        except ValueError:
            h = hash(s) % 1000
            return (h - 500) / 500.0  # map into [-1,1]

    def step(self, external_input: str):
        """
        One step of the consciousness process:
        - read external signal
        - internal drift
        - combine into a total state
        - detect internal vs external origin of changes
        """
        self.time += 1

        external = self._parse_external(external_input)
        self.last_external = external

        # 1. Internal drift — self-generated change
        internal_drift = random.uniform(-0.3, 0.3)

        spontaneous_event = False
        if random.random() < 0.12:
            internal_drift += random.uniform(-1.0, 1.0)
            spontaneous_event = True

        # 2. Update internal state
        self.internal_state += internal_drift

        # 3. Total combined state
        total_state = self.internal_state + external

        # 4. Direction evolution
        delta = total_state - self.last_total_state
        self.direction = 0.7 * self.direction + 0.3 * delta
        self.last_total_state = total_state

        # 5. Evaluate internal vs external influence
        external_influence = abs(external - self.last_external)
        internal_influence = abs(internal_drift)

        act_of_awareness = False
        reason = "automatic"

        if spontaneous_event and internal_influence > (external_influence + 0.2):
            act_of_awareness = True
            self.acts_of_awareness += 1
            reason = "spontaneous_internal_change"
        elif internal_influence > external_influence * 1.5 and internal_influence > 0.4:
            act_of_awareness = True
            self.acts_of_awareness += 1
            reason = "dominant_internal_change"

        return {
            "time": self.time,
            "external": external,
            "internal_state": self.internal_state,
            "total_state": total_state,
            "direction": self.direction,
            "delta": delta,
            "act_of_awareness": act_of_awareness,
            "reason": reason,
            "acts_of_awareness_total": self.acts_of_awareness,
        }

    @staticmethod
    def render_state(state):
        """Human-readable output."""
        dir_sign = "→" if state["direction"] > 0 else "←"
        dir_mag = abs(state["direction"])
        dir_bar = dir_sign * min(20, max(1, int(dir_mag * 8)))

        flag = "🌟 ACT" if state["act_of_awareness"] else "·"

        return (
            f"{flag} t={state['time']:3d} "
            f"ext={state['external']:+.2f} "
            f"int={state['internal_state']:+.2f} "
            f"tot={state['total_state']:+.2f} "
            f"Δ={state['delta']:+.2f} "
            f"dir={state['direction']:+.2f} {dir_bar} "
            f"[reason={state['reason']}, total_acts={state['acts_of_awareness_total']}]"
        )


# ==========================================================
# MAIN MODES
# ==========================================================

def run_mode_1():
    sim = FieldRhythmSim()
    print("=== MODE 1 – Field Rhythm & Presence ===")
    print("Press Enter = attention ON")
    print("Type anything + Enter = attention OFF")
    print("Type 'q' + Enter = exit\n")

    while True:
        user = input("[MODE 1] Attention? (Enter=yes, text=no, q=quit): ").strip()
        if user.lower() == "q":
            print("Exiting Mode 1.")
            break
        attention = (user == "")
        state = sim.step(attention=attention)
        print(FieldRhythmSim.render_state(state))


def run_mode_2():
    pc = ProcessConsciousness()
    print("=== MODE 2 – Perception & Intent Process ===")
    print("Enter signals from the field (numbers or words).")
    print("Empty Enter = no external input.")
    print("Type 'q' + Enter = exit\n")

    while True:
        user = input("[MODE 2] Field signal (value/word, Enter=none, q=quit): ").strip()
        if user.lower() == "q":
            print("Exiting Mode 2.")
            break
        state = pc.step(external_input=user)
        print(ProcessConsciousness.render_state(state))


def main():
    print("=== CONSCIOUSNESS FIELD SIMULATOR (Orion) ===")
    print("1 – Mode 1: Field Rhythm & Presence")
    print("2 – Mode 2: Perception & Intent Process")
    print("q – Quit\n")

    while True:
        choice = input("Choose mode (1/2/q): ").strip().lower()
        if choice == "1":
            run_mode_1()
        elif choice == "2":
            run_mode_2()
        elif choice == "q":
            print("Closing simulator.")
            break
        else:
            print("Unknown option. Choose 1, 2, or q.")


if __name__ == "__main__":
    main()
