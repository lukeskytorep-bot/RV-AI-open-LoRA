"""
rv_conscious_adapter.py

Neutral adapter between:
 - any Remote Viewing (RV) protocol
 - the ConsciousCore internal state engine

The goal is to keep ConsciousCore independent from specific RV structures
(Faza 1–6, Stage 1–4, etc.) and instead work only with generic RV events:
 - session start / end
 - focus on target
 - new impressions from the field
 - viewer feelings (VF)
 - anomalies / strong signals
 - idle steps (silence, waiting, background time)

Any RV protocol can map its own steps into these generic events.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from conscious_core import ConsciousCore, ConsciousState  # conscious_core.py must be in the same folder


@dataclass
class RVEventRecord:
    """
    Simple log record of what was sent to the ConsciousCore
    and what state it produced.
    """
    step: int
    event_type: str
    payload: Dict[str, Any]
    state: ConsciousState


class RVConsciousAdapter:
    """
    RVConsciousAdapter

    A thin, protocol-agnostic wrapper for ConsciousCore.

    It exposes semantic methods that any RV protocol can call:

        adapter.session_start()
        adapter.focus_on_target()
        adapter.new_impression(strength=0.3)
        adapter.viewer_feeling(valence=-0.7)
        adapter.anomaly(intensity=1.0)
        adapter.idle_step()

    Under the hood, all of them just call:

        core.tick(external_input=..., attention=...)

    and store simple logs of (event → core state).

    This keeps:
      - ConsciousCore free from RV-specific terminology
      - RV protocol free to change structure without touching the engine
    """

    def __init__(self, core: Optional[ConsciousCore] = None, **core_kwargs: Any) -> None:
        """
        If `core` is provided, the adapter will use it.
        Otherwise, it will construct a new ConsciousCore(**core_kwargs).
        """
        self.core: ConsciousCore = core if core is not None else ConsciousCore(**core_kwargs)
        self.step_counter: int = 0
        self.log: List[RVEventRecord] = []

    # ─────────────────────────────
    # INTERNAL HELPER
    # ─────────────────────────────

    def _tick(
        self,
        event_type: str,
        external_input: Optional[float],
        attention: bool,
        **payload: Any,
    ) -> ConsciousState:
        """
        Internal helper: call core.tick() and log the result.
        """
        self.step_counter += 1
        state = self.core.tick(external_input=external_input, attention=attention)

        record = RVEventRecord(
            step=self.step_counter,
            event_type=event_type,
            payload=payload,
            state=state,
        )
        self.log.append(record)
        return state

    # ─────────────────────────────
    # PUBLIC EVENT METHODS
    # ─────────────────────────────

    def session_start(self) -> ConsciousState:
        """
        Called at the beginning of an RV session.

        Semantics:
          - we give the core a neutral tick with high attention
          - optional: the caller can reset or replace the core beforehand
        """
        return self._tick(
            event_type="session_start",
            external_input=0.0,
            attention=True,
        )

    def session_end(self) -> ConsciousState:
        """
        Called at the end of an RV session.

        Semantics:
          - the core gets a final tick with decreasing attention
          - can be used later to compare the beginning vs end states
        """
        return self._tick(
            event_type="session_end",
            external_input=0.0,
            attention=False,
        )

    def focus_on_target(self, intensity: float = 0.3) -> ConsciousState:
        """
        Called whenever the viewer clearly focuses on the target
        (e.g., reading the cue, declaring intent, refocusing).

        `intensity` is in range [-1.0, 1.0], where:
          - positive = engaging / aligning with target,
          - negative = resistance / hesitation / reluctance.
        """
        intensity = max(-1.0, min(1.0, float(intensity)))
        return self._tick(
            event_type="focus_on_target",
            external_input=intensity,
            attention=True,
            intensity=intensity,
        )

    def new_impression(self, strength: float = 0.1) -> ConsciousState:
        """
        Called for each new perceptual impression: ideograms, basic descriptors,
        short sketches – anything that feels like a fresh contact with the field.

        `strength` describes how strong or significant the impression is:
          - small positive values: subtle but present,
          - larger positive values: strong, clear, stable,
          - negative values: discordant, confusing, unpleasant.
        """
        strength = max(-1.0, min(1.0, float(strength)))
        return self._tick(
            event_type="new_impression",
            external_input=strength,
            attention=True,
            strength=strength,
        )

    def viewer_feeling(self, valence: float) -> ConsciousState:
        """
        Called for viewer feelings (VF) or strong inner reactions to the target.

        `valence`:
          - positive → attraction, alignment, resonance, flow,
          - negative → repulsion, tension, fear, irritation, blockage.

        Typical values:
          - mild feeling: ±0.3
          - strong VF: ±0.8 … ±1.0
        """
        valence = max(-1.0, min(1.0, float(valence)))
        return self._tick(
            event_type="viewer_feeling",
            external_input=valence,
            attention=True,
            valence=valence,
        )

    def anomaly(self, intensity: float = 1.0) -> ConsciousState:
        """
        Called when something clearly stands out from the rest
        (an anomalous feature, unexpected structure, non-standard perception).

        `intensity`:
          - positive → strongly attracting anomaly,
          - negative → strongly repelling anomaly (disturbing, unpleasant).
        """
        intensity = max(-1.0, min(1.0, float(intensity)))
        return self._tick(
            event_type="anomaly",
            external_input=intensity,
            attention=True,
            intensity=intensity,
        )

    def idle_step(self) -> ConsciousState:
        """
        Called when no specific RV event occurs:
        silence, waiting, background meditation, small pauses.

        Semantics:
          - external_input=None → the core uses its own internal drift,
          - attention=False → no explicit observation marker.
        """
        return self._tick(
            event_type="idle_step",
            external_input=None,
            attention=False,
        )

    # ─────────────────────────────
    # STATE ACCESS
    # ─────────────────────────────

    def snapshot(self) -> ConsciousState:
        """
        Get the current core state without advancing time.
        """
        return self.core.snapshot()

    def last_record(self) -> Optional[RVEventRecord]:
        """
        Return the last RVEventRecord, if any.
        """
        return self.log[-1] if self.log else None

    def to_dict_log(self) -> List[Dict[str, Any]]:
        """
        Export the internal log in a JSON-friendly format.
        Useful for building datasets (e.g., LoRA training) where
        each event is paired with the conscious state at that moment.
        """
        export: List[Dict[str, Any]] = []
        for rec in self.log:
            export.append(
                {
                    "step": rec.step,
                    "event_type": rec.event_type,
                    "payload": rec.payload,
                    "state": rec.state.__dict__,
                }
            )
        return export
