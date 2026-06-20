import re

with open('backend/app/llm.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove MockLLMClient class
content = re.sub(r'class MockLLMClient:.*?# Instantiate LLM Clients', '# Instantiate LLM Clients', content, flags=re.DOTALL)

# 2. Update _resolve_llm_mode to not return mock
content = content.replace('return "mock"', 'raise ValueError("No LLM backend available (Gemini/Groq/Local). Please set an API key.")')

# 3. Remove mock_llm_client from instantiations
content = content.replace('mock_llm_client = MockLLMClient()\n', '')
content = content.replace('"mock": mock_llm_client,\n', '')
content = content.replace('return mock_llm_client', 'raise ValueError("LLM fallback failed.")')

# 4. Remove fallback calls in LocalLLMClient, GeminiLLMClient, GroqLLMClient
content = content.replace('logger.warning("Local pipeline not available. Falling back to Mock generator.")\n            return mock_llm_client.generate(system_prompt, user_prompt)', 'raise RuntimeError("Local pipeline not available.")')
content = content.replace('return mock_llm_client.generate(system_prompt, user_prompt)', 'raise RuntimeError("LLM generation failed.")')

# 5. Fix GeminiLLMClient
gemini_new = '''class GeminiLLMClient:
    """Google Gemini API — free tier, fast (~1-3s). Get key: https://aistudio.google.com/apikey"""
    
    def __init__(self):
        import httpx
        self.client = httpx.Client(timeout=90.0)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
        }
        res = self.client.post(url, params={"key": GEMINI_API_KEY}, json=payload)
        res.raise_for_status()
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
'''
content = re.sub(r'class GeminiLLMClient:.*?class GroqLLMClient:', gemini_new + '\n\nclass GroqLLMClient:', content, flags=re.DOTALL)

# 6. Fix SentenceEmbeddingEngine
embedding_new = '''class SentenceEmbeddingEngine:
    def __init__(self):
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Initializing SentenceTransformer: all-MiniLM-L6-v2")
            self.model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
            logger.info("SentenceTransformer loaded successfully.")
        except Exception as e:
            logger.error(f"Could not load SentenceTransformer: {e}")
            raise

    def get_embedding(self, text: str) -> bytes:
        import numpy as np
        embedding = self.model.encode(text)
        return np.array(embedding, dtype=np.float32).tobytes()

    def compute_similarity(self, emb_a: bytes, emb_b: bytes) -> float:
        import numpy as np
        if not emb_a or not emb_b:
            return 0.0
        arr_a = np.frombuffer(emb_a, dtype=np.float32)
        arr_b = np.frombuffer(emb_b, dtype=np.float32)
        if len(arr_a) != len(arr_b) or len(arr_a) == 0:
            return 0.0
        norm_a = np.linalg.norm(arr_a)
        norm_b = np.linalg.norm(arr_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(arr_a, arr_b) / (norm_a * norm_b))
'''
content = re.sub(r'class SentenceEmbeddingEngine:.*?# Initialize Embedding Engine', embedding_new + '\n# Initialize Embedding Engine', content, flags=re.DOTALL)

# Also force llm_mode resolution to strictly be 'gemini' if auto is set and mock is disabled
content = re.sub(r'LLM_MODE = os.environ.get\("LLM_MODE", diagnostics\["default_mode"\]\).lower\(\)', 'LLM_MODE = os.environ.get("LLM_MODE", "gemini").lower()', content)

with open('backend/app/llm.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated llm.py successfully!')
