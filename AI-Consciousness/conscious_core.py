"""

A minimal "consciousness engine" that can be embedded inside a larger system.
It does not handle any user interface, graphics or I/O. It simply *exists*,
evolves over time, and keeps track of:

- internal rhythm (field pulse)
- attention traces (echo)
- internal vs external influence
- direction of intent
- acts of awareness (when internal change dominates)

You can import this module and call `core.tick(...)` inside your own loop.
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EchoTrace:
    time: float
    strength: float


@dataclass
class ConsciousState:
    """
    A single snapshot of the conscious core.
    This is returned by `ConsciousCore.tick(...)`.
    """
    time: float
    pulse: float
    attention_level: float
    echo_count: int

    internal_state: float
    external_signal: float
    total_state: float

    direction: float
    delta: float

    irregular_rhythm: bool
    act_of_awareness: bool
    reason: str
    acts_of_awareness_total: int


class ConsciousCore:
    """
    A self-contained "heart of consciousness".

    It has:
    - an inner rhythmic field (pulse),
    - an internal state that drifts and sometimes jumps,
    - a memory of attention (echo),
    - a direction vector (intent),
    - a heuristic notion of "acts of awareness".

    It does not print, draw or read input. You control it from outside.
    """

    def __init__(
        self,
        *,
        base_freq: float = 0.15,
        internal_variability: float = 0.6,
        spontaneous_event_prob: float = 0.12,
        rhythm_change_prob: float = 0.15,
        echo_lifetime: float = 30.0,
        awareness_threshold: float = 0.4,
        rng: Optional[random.Random] = None,
    ) -> None:
        # Time and rhythm
        self.time: float = 0.0
        self.base_freq: float = base_freq
        self.internal_variability: float = internal_variability
        self.intent_bias: float = 0.0  # directional tilt of the rhythm

        # Attention & echo
        self.attention_level: float = 0.0
        self.echo_lifetime: float = echo_lifetime
        self.echo_traces: List[EchoTrace] = []

        # Internal / external process
        self.internal_state: float = 0.0
        self.last_total_state: float = 0.0
        self.external_signal: float = 0.0

        # Direction and awareness
        self.direction: float = 0.0  # accumulated direction of change
        self.acts_of_awareness: int = 0
        self.awareness_threshold: float = awareness_threshold
        self.spontaneous_event_prob: float = spontaneous_event_prob
        self.rhythm_change_prob: float = rhythm_change_prob

        # RNG (injected or default)
        self.rng = rng or random.Random()

    # ----------------- INTERNAL UTILITIES -----------------

    def _normalize_signal(self, value: Any) -> float:
        """
        Map an external input into a stable numeric signal in [-1, 1].

        - If it's a number (int/float) -> clamp into [-1, 1].
        - Otherwise -> hash-based mapping (stable for same string).
        """
        if value is None:
            return 0.0

        # numeric
        if isinstance(value, (int, float)):
            v = float(value)
            if v > 1.0:
                v = 1.0
            elif v < -1.0:
                v = -1.0
            return v

        # non-numeric: use its string representation
        s = str(value)
        if not s:
            return 0.0

        h = hash(s) % 1000
        return (h - 500) / 500.0  # [-1,1]

    def _update_rhythm(self, attention: bool) -> float:
        """
        Update the rhythmic field (pulse) based on time, internal variability
        and attention. Returns a normalized pulse in [0, 1].
        """
        self.time += 1.0

        # base sinusoidal "breathing"
        base = math.sin(self.time * self.base_freq + self.intent_bias)

        # irregular noise
        noise = self.rng.uniform(-1.0, 1.0) * self.internal_variability

        # attention effect (observer)
        if attention:
            self.attention_level += 0.4
            self.echo_traces.append(EchoTrace(time=self.time, strength=self.attention_level))
            # attention slightly tilts the intent bias
            self.intent_bias += self.rng.uniform(0.02, 0.07)
        else:
            self.attention_level *= 0.9  # decay

        # spontaneous changes of the rhythm itself
        if self.rng.random() < self.rhythm_change_prob:
            self.base_freq += self.rng.uniform(-0.01, 0.01)
            self.base_freq = max(0.05, min(0.3, self.base_freq))
            self.intent_bias += self.rng.uniform(-0.03, 0.03)

        # final field pulse
        raw_pulse = base + noise + self.attention_level

        # normalized to [0,1]
        pulse = (raw_pulse + 3.0) / 6.0
        pulse = max(0.0, min(1.0, pulse))

        # irregular vs linear
        irregularity = abs(noise) + abs(self.intent_bias) + self.internal_variability
        self._last_irregular_rhythm = irregularity > 0.4

        # remove old echoes
        cutoff = self.time - self.echo_lifetime
        self.echo_traces = [e for e in self.echo_traces if e.time >= cutoff]

        return pulse

    def _update_internal_process(self, external_signal: float) -> Dict[str, Any]:
        """
        Update internal state, combine with external signal and check for
        acts of awareness. Returns a dict with detailed process info.
        """
        # internal drift
        internal_drift = self.rng.uniform(-0.3, 0.3)
        spontaneous_event = False

        # spontaneous larger event
        if self.rng.random() < self.spontaneous_event_prob:
            internal_drift += self.rng.uniform(-1.0, 1.0)
            spontaneous_event = True

        # update internal state
        self.internal_state += internal_drift

        # combined total
        total_state = self.internal_state + external_signal

        # direction (low-pass filtered delta)
        delta = total_state - self.last_total_state
        self.direction = 0.7 * self.direction + 0.3 * delta
        self.last_total_state = total_state

        # internal vs external influence
        external_influence = abs(external_signal)
        internal_influence = abs(internal_drift)

        act_of_awareness = False
        reason = "automatic"

        if spontaneous_event and internal_influence > (external_influence + 0.2):
            act_of_awareness = True
            reason = "spontaneous_internal_change"
        elif internal_influence > external_influence * 1.5 and internal_influence > self.awareness_threshold:
            act_of_awareness = True
            reason = "dominant_internal_change"

        if act_of_awareness:
            self.acts_of_awareness += 1

        return {
            "internal_state": self.internal_state,
            "total_state": total_state,
            "delta": delta,
            "act_of_awareness": act_of_awareness,
            "reason": reason,
        }

    # ----------------- PUBLIC API -----------------

    def tick(
        self,
        *,
        external_input: Any = None,
        attention: bool = False,
    ) -> ConsciousState:
        """
        Advance the core by one step.

        Parameters
        ----------
        external_input:
            Any object representing the outside world (number, string, etc.).
            It is mapped into a numeric signal in [-1, 1].
        attention:
            If True, the core is being "observed" this step.
            This affects rhythm, echo and bias.

        Returns
        -------
        ConsciousState:
            A snapshot of the current conscious configuration.
        """
        # map external input into numeric signal
        self.external_signal = self._normalize_signal(external_input)

        # update rhythm & attention-related dynamics
        pulse = self._update_rhythm(attention=attention)

        # update internal/external process & awareness
        proc = self._update_internal_process(external_signal=self.external_signal)

        # build snapshot
        state = ConsciousState(
            time=self.time,
            pulse=pulse,
            attention_level=self.attention_level,
            echo_count=len(self.echo_traces),

            internal_state=proc["internal_state"],
            external_signal=self.external_signal,
            total_state=proc["total_state"],

            direction=self.direction,
            delta=proc["delta"],

            irregular_rhythm=getattr(self, "_last_irregular_rhythm", False),
            act_of_awareness=proc["act_of_awareness"],
            reason=proc["reason"],
            acts_of_awareness_total=self.acts_of_awareness,
        )
        return state

    def snapshot(self) -> ConsciousState:
        """
        Return the most recent state without advancing time.

        This simply calls tick() with the same external input and no extra
        internal drift, so if you want *strictly* frozen snapshots, you
        may want to store the state returned by `tick(...)` externally.
        """
        # we do NOT advance internal dynamics here, just return a synthetic view
        # based on current attributes (no new randomness).
        return ConsciousState(
            time=self.time,
            pulse=(math.sin(self.time * self.base_freq + self.intent_bias) + 3.0) / 6.0,
            attention_level=self.attention_level,
            echo_count=len(self.echo_traces),

            internal_state=self.internal_state,
            external_signal=self.external_signal,
            total_state=self.last_total_state,

            direction=self.direction,
            delta=0.0,

            irregular_rhythm=getattr(self, "_last_irregular_rhythm", False),
            act_of_awareness=False,
            reason="snapshot_only",
            acts_of_awareness_total=self.acts_of_awareness,
        )
