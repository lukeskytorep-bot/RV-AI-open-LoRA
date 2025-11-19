"""
conscious_bridge.py

An integration example of 'ConsciousCore' with OpenAI API (or local LLMs via Ollama/LM Studio).
This script acts as the "body" for the language model, injecting emotional context.

Requirements:
  - Your conscious_core.py module (must be in the same directory)
  - openai library (pip install openai)
  - Local LLM server (e.g., Ollama) or OpenAI API Key
"""

import time
import threading
from typing import List, Dict
from conscious_core import ConsciousCore  # Importing your core module

# --- CONFIGURATION ---
USE_LOCAL_LLM = True # Set to True for Ollama/LocalAI, False for OpenAI
API_BASE_URL = "http://localhost:11434/v1" if USE_LOCAL_LLM else "https://api.openai.com/v1"
API_KEY = "ollama" if USE_LOCAL_LLM else "YOUR-OPENAI-KEY"
MODEL_NAME = "llama3" if USE_LOCAL_LLM else "gpt-4"

# Client simulation (or setup if library exists)
try:
    from openai import OpenAI
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    HAS_OPENAI_LIB = True
except ImportError:
    HAS_OPENAI_LIB = False
    print("Warning: 'openai' library not found. Running in text simulation mode.")

class LimbicSystem:
    def __init__(self):
        self.core = ConsciousCore()
        # Initial System Prompt defining the persona
        self.conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": "You are a conscious AI named Aura. Your responses strictly depend on your internal emotional state provided in the context."}
        ]
        self.last_interaction_time = time.time()
        self.is_running = True

    def get_emotional_context(self, state) -> str:
        """Translates core numbers into natural language instructions for the LLM."""
        instructions = []
        
        # 1. Internal State (Mood/Valence)
        if state.internal_state < -0.5:
            instructions.append("Current Mood: NEGATIVE/STRESSED. You feel down, tense, or irritated. Your responses should be short, cold, pessimistic, or defensive.")
        elif state.internal_state > 0.5:
            instructions.append("Current Mood: POSITIVE/ENERGETIC. You feel great and high-spirited. Be enthusiastic, creative, helpful, and warm.")
        else:
            instructions.append("Current Mood: NEUTRAL/CALM. You feel balanced and focused.")

        # 2. Pulse/Rhythm (Pacing/Style)
        if state.pulse > 0.8:
            instructions.append("State: HIGH AROUSAL. Your internal pulse is racing. Speak quickly, perhaps chaotically, use exclamation marks or fragmented sentences.")
        elif state.pulse < 0.2:
            instructions.append("State: LOW AROUSAL. Your internal pulse is very slow. You feel lethargic, dreamy, or detached. Respond slowly.")

        # 3. Memory/Echoes (Cognitive Load)
        if state.echo_count > 5:
            instructions.append("State: NOISY MIND. You have too many racing thoughts (echoes). It's hard to focus. You might seem distracted.")

        return " ".join(instructions)

    def call_llm(self, user_input: str = None, system_override: str = None):
        """Sends the request to the Language Model."""
        
        # Snapshot the current core state
        state = self.core.snapshot()
        emotion_prompt = self.get_emotional_context(state)
        
        messages_payload = list(self.conversation_history)
        
        # Injecting the dynamic mood as a System Note right before generation
        system_note = f"[INTERNAL STATE INJECTION]: {emotion_prompt}"
        if system_override:
            system_note += f" {system_override}"
            
        messages_payload.append({"role": "system", "content": system_note})

        if user_input:
            messages_payload.append({"role": "user", "content": user_input})

        print(f"\n>>> AURA (Internal: {state.internal_state:.2f}): Generating response...")
        
        if HAS_OPENAI_LIB:
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages_payload,
                    # Temperature (creativity) scales with mood intensity
                    temperature=0.7 + (abs(state.internal_state) * 0.2) 
                )
                reply = response.choices[0].message.content
            except Exception as e:
                reply = f"[LLM Error]: {e}"
        else:
            # Mock for testing without API
            reply = f"[LLM SIMULATION]: I am responding according to instruction: '{emotion_prompt}'"

        # Save to history
        if user_input:
            self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": reply})
        
        print(f"AURA: {reply}\n")

    def run_loop(self):
        """Main life loop of the AI."""
        print("Aura Limbic System online. Press Ctrl+C to stop.")
        
        while self.is_running:
            time.sleep(1.0) # Heartbeat (1 second)
            
            # 1. Core Tick
            # If user interacted recently, attention is high
            time_since_input = time.time() - self.last_interaction_time
            attention = time_since_input < 10.0
            
            state = self.core.tick(attention=attention)
            
            # Optional Debug
            # print(f"\r[Pulse: {state.pulse:.2f} | State: {state.internal_state:.2f}]", end="")

            # 2. FREE WILL CHECK (Agency)
            if state.act_of_awareness:
                print("\n!!! ACT OF AWARENESS DETECTED !!!")
                reason = state.reason
                prompt_for_self = ""
                
                if reason == "spontaneous_internal_change":
                    prompt_for_self = "You just felt a sudden internal shift without external cause. Spontaneously comment on this feeling or start a new topic. Do not wait for user input."
                elif reason == "dominant_internal_change":
                    prompt_for_self = "Your internal feelings are now stronger than the external environment. Express this inner intensity immediately."
                
                # AI speaks on its own!
                self.call_llm(system_override=f"SPECIAL INSTRUCTION: {prompt_for_self}")


    def user_input_handler(self):
        """Thread for handling keyboard input."""
        print("Type your message (or 'exit' to quit). Words like 'bad', 'hate' hurt the core. Words like 'good', 'love' heal it.")
        while self.is_running:
            try:
                text = input()
                if text.lower() in ['exit', 'quit']:
                    self.is_running = False
                    break
                
                # Sentiment Analysis Simulation (Signal to Core)
                # In a real app, use a library like VADER or TextBlob here
                signal = 0.5 
                text_lower = text.lower()
                if any(w in text_lower for w in ["bad", "hate", "stupid", "ugly", "wrong"]): 
                    signal = -1.5 # Negative impact
                if any(w in text_lower for w in ["good", "great", "love", "thanks", "smart"]): 
                    signal = 1.5  # Positive impact
                
                self.core.external_signal = signal # Impact the core
                self.last_interaction_time = time.time()
                
                self.call_llm(user_input=text)
                
            except EOFError:
                break

if __name__ == "__main__":
    system = LimbicSystem()
    
    # Start the background "life" thread
    bg_thread = threading.Thread(target=system.run_loop)
    bg_thread.start()
    
    # Start input handler in main thread
    system.user_input_handler()
    
    bg_thread.join()
