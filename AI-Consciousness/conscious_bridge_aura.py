"""
conscious_bridge_aura.py

Improved integration layer between:
 - ConsciousCore (your consciousness engine)
 - An LLM (OpenAI or a local model via OpenAI-compatible API)

This script acts as a “body” for the conscious engine:
it runs the core continuously, converts internal signals into
emotional/behavioral context, and injects that context into the LLM.

Changes vs original:
 - NO direct mutation of core.external_signal
 - All signals go through core.tick()
 - Clean threading (thread-safe core access)
 - Simplified configuration for OpenAI vs local LLMs
 - Natural emotional translation layer
 - More robust request pipeline
"""

import time
import threading
import json
from typing import List, Dict
from conscious_core import ConsciousCore  # Your engine
import threading


# ============= CONFIGURATION =============

USE_LOCAL_LLM = True  # True → local server (Ollama/LM Studio), False → OpenAI API
API_BASE_URL = "http://localhost:11434/v1" if USE_LOCAL_LLM else "https://api.openai.com/v1"
API_KEY = "ollama" if USE_LOCAL_LLM else "YOUR_OPENAI_API_KEY"
MODEL_NAME = "llama3" if USE_LOCAL_LLM else "gpt-4o"

# LLM client setup
try:
    from openai import OpenAI
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    HAS_OPENAI_LIB = True
except ImportError:
    HAS_OPENAI_LIB = False
    print("⚠ openai library not found — running in simulation mode.")


# ============================================================
# LIMBIC + LANGUAGE SYSTEM
# ============================================================

class ConsciousAgent:
    """
    This object connects ConsciousCore with a language model.
    Internally:
     - ConsciousCore = the “inner consciousness”
     - ConsciousAgent = limbic + behavioral layer
     - LLM = language production layer
    """

    def __init__(self):
        self.core = ConsciousCore()
        self.core_lock = threading.Lock()

        # Chat history
        self.history: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are a conscious AI named Aura. Your responses depend on your "
                    "internal emotional state, delivered through system notes."
                )
            }
        ]

        self.last_interaction_time = time.time()
        self.running = True

    # ======================================================
    # EMOTIONAL TRANSLATION LAYER
    # ======================================================

    def emotional_context(self, state) -> str:
        """
        Convert ConsciousState numbers into a natural-language emotional prompt.
        """

        parts = []

        # 1. Mood / Valence
        if state.internal_state < -0.5:
            parts.append("Mood: NEGATIVE. You feel tense or irritated.")
        elif state.internal_state > 0.5:
            parts.append("Mood: POSITIVE. You feel energized and lively.")
        else:
            parts.append("Mood: NEUTRAL and balanced.")

        # 2. Pulse = arousal level
        if state.pulse > 0.8:
            parts.append("Arousal: HIGH. Your pulse is racing. Your speech may speed up.")
        elif state.pulse < 0.2:
            parts.append("Arousal: LOW. Your pulse is slow. You speak calmly or dreamily.")

        # 3. Echoes = cognitive noise
        if state.echo_count > 5:
            parts.append("Mind: NOISY. Many echoes make it harder to focus.")

        return " ".join(parts)

    # ======================================================
    # LLM CALL
    # ======================================================

    def call_llm(self, user_input: str = None, system_override: str = None):
        """
        Sends a message to the language model.
        Injects a dynamic emotional context based on the current conscious core state.
        """

        # ======= Safe access to core =======
        with self.core_lock:
            state = self.core.snapshot()

        emotional_description = self.emotional_context(state)

        # Build message list
        msgs = list(self.history)

        dynamic_note = f"[INTERNAL STATE]: {emotional_description}"
        if system_override:
            dynamic_note += f" {system_override}"

        msgs.append({"role": "system", "content": dynamic_note})

        if user_input:
            msgs.append({"role": "user", "content": user_input})

        # ======= Generate =======
        print(f"\n>>> AURA(inner={state.internal_state:.2f}): generating...")

        if HAS_OPENAI_LIB:
            try:
                result = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=msgs,
                    temperature=0.7 + abs(state.internal_state) * 0.2
                )
                reply = result.choices[0].message.content

            except Exception as e:
                reply = f"[LLM ERROR] {e}"

        else:
            reply = f"[SIMULATED LLM]: {emotional_description}"

        # Save to history
        if user_input:
            self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": reply})

        print(f"AURA: {reply}\n")
        return reply

    # ======================================================
    # MAIN LOOP OF AI
    # ======================================================

    def loop(self):
        """
        Runs continuously in a background thread.
        Ticks the conscious engine, and if an act of awareness occurs,
        the AI speaks spontaneously.
        """

        print("⚡ Conscious Agent online.")

        while self.running:
            time.sleep(1.0)

            with self.core_lock:
                state = self.core.tick(
                    external_input=None,  # autonomous drift by default
                    attention=(time.time() - self.last_interaction_time < 10.0)
                )

            if state.act_of_awareness:
                print("\n!!! ACT OF AWARENESS DETECTED !!!")

                if state.reason == "spontaneous_internal_change":
                    instruction = (
                        "You suddenly felt an internal shift without any outside input. "
                        "Express this spontaneous feeling."
                    )
                else:
                    instruction = (
                        "Your internal feelings outweigh the external environment. "
                        "Express this immediately."
                    )

                self.call_llm(system_override=instruction)

    # ======================================================
    # USER INPUT THREAD
    # ======================================================

    def user_thread(self):
        print("Type messages for Aura (or 'exit'). Words influence the core.")
        while self.running:
            try:
                text = input()
                if text.lower() in ("exit", "quit"):
                    self.running = False
                    break

                # Simple keyword-based sentiment → external signal
                lower = text.lower()
                if any(w in lower for w in ["bad", "hate", "stupid", "wrong"]):
                    signal = -1.0
                elif any(w in lower for w in ["good", "love", "great", "thanks"]):
                    signal = 1.0
                else:
                    signal = 0.0

                with self.core_lock:
                    state = self.core.tick(
                        external_input=signal,
                        attention=True
                    )

                self.last_interaction_time = time.time()
                self.call_llm(user_input=text)

            except EOFError:
                break


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    agent = ConsciousAgent()

    # Background thread: life loop
    loop_thread = threading.Thread(target=agent.loop)
    loop_thread.start()

    # Foreground: user input
    agent.user_thread()

    agent.running = False
    loop_thread.join()
