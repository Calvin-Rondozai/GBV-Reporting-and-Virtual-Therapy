import os
import re
import torch
from typing import List, Dict

# =========================
# Dependencies
# =========================
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print(
        "ERROR: transformers library not installed. Install with: pip install transformers torch"
    )


# =========================
# Conversation Context
# =========================
class ConversationContext:
    def __init__(self, max_history: int = 4):
        self.history: List[Dict[str, str]] = []
        self.max_history = max_history
        self.detected_emotions: List[str] = []

    def add_exchange(self, user: str, assistant: str):
        self.history.append({"user": user, "assistant": assistant})
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def add_emotion(self, emotion: str):
        if emotion not in self.detected_emotions:
            self.detected_emotions.append(emotion)


# =========================
# Emotion Detection
# =========================
class EmotionDetector:
    EMOTIONS = {
        "sadness": ["sad", "down", "unhappy", "crying"],
        "anxiety": ["anxious", "worried", "panic", "overwhelmed"],
        "anger": ["angry", "frustrated"],
        "loneliness": ["lonely", "alone", "ignored"],
        "joy": ["happy", "relieved"],
    }

    CRISIS = [
        "suicide",
        "kill myself",
        "self harm",
        "end my life",
        "don't want to live",
    ]

    @staticmethod
    def detect_emotions(message: str) -> List[str]:
        msg = message.lower()
        found = [
            e
            for e, keys in EmotionDetector.EMOTIONS.items()
            if any(k in msg for k in keys)
        ]
        return found if found else ["neutral"]

    @staticmethod
    def is_crisis(message: str) -> bool:
        msg = message.lower()
        return any(k in msg for k in EmotionDetector.CRISIS)


# =========================
# Input Sanitization
# =========================
def sanitize_user_input(text: str) -> str:
    text = re.sub(r"\[/?INST\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"you are a .*? therapist.*", "", text, flags=re.IGNORECASE)
    return text.strip()


# =========================
# Therapy Service
# =========================
class TherapyService:
    SYSTEM_PROMPT = (
        "You are a calm, supportive listener. "
        "Respond briefly with warmth and clarity. "
        "Do not explain rules or roles."
    )

    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.context = ConversationContext()
        self.detector = EmotionDetector()
        self.model = None
        self.tokenizer = None
        self.model_type = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_model()

    # =========================
    # Model Loading
    # =========================
    def _load_model(self):
        """Load the GPT2-based Transformers model from Models directory"""
        if not TRANSFORMERS_AVAILABLE:
            print("ERROR: transformers library not available")
            return

        if not os.path.exists(self.model_dir):
            print(f"ERROR: Model directory not found: {self.model_dir}")
            return

        config_path = os.path.join(self.model_dir, "config.json")
        model_path = os.path.join(self.model_dir, "model.safetensors")

        if not os.path.exists(config_path):
            print(f"ERROR: config.json not found in {self.model_dir}")
            return

        if not os.path.exists(model_path):
            print(f"ERROR: model.safetensors not found in {self.model_dir}")
            return

        try:
            print(f"Loading model from: {self.model_dir}")
            print("  - Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)

            print("  - Loading model...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_dir,
                torch_dtype=torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=False,
            )

            # Move to device if not using device_map
            if not torch.cuda.is_available():
                self.model = self.model.to(self.device)

            # Set pad token if not set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Set model to evaluation mode
            self.model.eval()

            self.model_type = "transformers"
            device_name = "GPU" if torch.cuda.is_available() else "CPU"
            print(f"✓ Model loaded successfully on {device_name}")
            print(f"  Model type: GPT2LMHeadModel")
            print(f"  Vocab size: {self.model.config.vocab_size}")
            print(f"  Max context: {self.model.config.n_positions}")

        except Exception as e:
            print(f"ERROR: Failed to load model: {e}")
            import traceback

            traceback.print_exc()
            self.model = None
            self.tokenizer = None

    # =========================
    # Public Interface
    # =========================
    def generate_response(self, user_message: str) -> str:
        msg = sanitize_user_input(user_message)

        if msg.lower() in {"hi", "hello", "hey"}:
            return "Hello. I’m here with you. What would you like to talk about today?"

        if self.detector.is_crisis(msg):
            return self._crisis_response()

        emotions = self.detector.detect_emotions(msg)
        for e in emotions:
            self.context.add_emotion(e)

        if self.model:
            response = self._model_response(msg)
            if response:
                self.context.add_exchange(msg, response)
                return response

        response = self._fallback_response(emotions)
        self.context.add_exchange(msg, response)
        return response

    # =========================
    # Model Responses
    # =========================
    def _model_response(self, user_message: str) -> str:
        """Generate response using the Transformers model"""
        if self.model is None or self.tokenizer is None:
            return ""

        try:
            # Build prompt with conversation history
            prompt_parts = []

            # Add system instruction
            prompt_parts.append(self.SYSTEM_PROMPT)

            # Add recent conversation history (last 2 exchanges)
            for exchange in self.context.history[-2:]:
                prompt_parts.append(f"User: {exchange['user']}")
                prompt_parts.append(f"Assistant: {exchange['assistant']}")

            # Add current user message
            prompt_parts.append(f"User: {user_message}")
            prompt_parts.append("Assistant:")

            prompt = "\n".join(prompt_parts)

            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=False,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.7,
                    top_p=0.9,
                    top_k=50,
                    do_sample=True,
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=3,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )

            # Decode the full output
            full_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract only the new response (after "Assistant:")
            if "Assistant:" in full_text:
                text = full_text.split("Assistant:")[-1].strip()
            else:
                # If "Assistant:" not found, extract everything after the prompt
                text = full_text[len(prompt) :].strip()

            # Clean and return
            cleaned = self._clean(text)

            # Basic validation
            if len(cleaned) < 10:
                return ""

            return cleaned

        except Exception as e:
            print(f"Error generating model response: {e}")
            import traceback

            traceback.print_exc()
            return ""

    # =========================
    # Utilities
    # =========================
    def _clean(self, text: str) -> str:
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return ". ".join(sentences[:3]) + "." if sentences else ""

    def _fallback_response(self, emotions: List[str]) -> str:
        if "sadness" in emotions:
            return "I’m really sorry you’re feeling this way. You’re not alone here."
        if "loneliness" in emotions:
            return "Feeling alone can be very painful. I’m here with you."
        if "anxiety" in emotions:
            return "It sounds overwhelming. We can take this one step at a time."
        return "Thank you for sharing. What feels most important right now?"

    def _crisis_response(self) -> str:
        return (
            "It sounds like you’re in a lot of pain, and your safety matters. "
            "If you’re in immediate danger, please contact local emergency services "
            "or reach out to someone you trust right now."
        )


# =========================
# Run CLI
# =========================
if __name__ == "__main__":
    service = TherapyService(model_dir="./models")
    print("Therapy Chatbot (type 'quit' to exit)\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "quit":
            break
        if not user_input:
            continue

        reply = service.generate_response(user_input)
        print(f"Therapist: {reply}\n")
