"""Quick test script to verify GGUF model is working"""
import os
import sys

# Try to import llama-cpp-python
try:
    from llama_cpp import Llama
    print("[OK] llama-cpp-python imported successfully")
except ImportError as e:
    print(f"[ERROR] llama-cpp-python not available: {e}")
    print("Install with: pip install llama-cpp-python")
    sys.exit(1)

# Find model file
models_dir = os.path.join(os.path.dirname(__file__), "Models")
model_paths = [
    os.path.join(models_dir, "SmolLM2-mental-health.Q4_K_M.gguf"),
    os.path.join(models_dir, "SmolLM2-mental-health.Q6_K.gguf"),
]

model_path = None
for path in model_paths:
    if os.path.exists(path):
        model_path = path
        print(f"[OK] Found model: {path}")
        break

if not model_path:
    print("[ERROR] No GGUF model found in Models directory")
    sys.exit(1)

# Load model
print(f"\nLoading model: {model_path}")
try:
    model = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=4,
        verbose=True,  # Enable verbose to see what's happening
    )
    print("[OK] Model loaded successfully!")
    print(f"Model context: {model.n_ctx} tokens\n")
except Exception as e:
    print(f"[ERROR] Error loading model: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test generation
test_prompt = """You are a professional therapist. Your role is to:
- Listen actively and respond directly to what the user says
- Stay focused on their message and answer their questions if asked
- Provide empathetic, supportive responses
- Keep responses concise (2-3 sentences maximum)
- Never go off-topic or change the subject
- If asked a question, answer it directly before offering additional support

User: I'm feeling really anxious today.
Therapist:"""

print("Testing generation with prompt:")
print(f"'{test_prompt[:100]}...'\n")

try:
    response = model(
        test_prompt,
        max_tokens=100,
        temperature=0.5,
        top_p=0.85,
        stop=["User:", "Human:"],
        echo=False,
    )
    
    print("Response type:", type(response))
    print("Response:", response)
    
    if isinstance(response, dict):
        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            if isinstance(choice, dict):
                text = choice.get("text", choice.get("content", str(choice)))
            else:
                text = str(choice)
            print(f"\n[OK] Generated text: {text}")
        else:
            print("[ERROR] No choices in response")
    elif isinstance(response, str):
        print(f"\n[OK] Generated text: {response}")
    else:
        print(f"[ERROR] Unexpected response format")
        
except Exception as e:
    print(f"[ERROR] Error during generation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[OK] Model test completed successfully!")
