import os
import re
import json
import logging
import datetime
import numpy as np
import torch
import psutil
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("creatoros.llm")

# Model Maps
# Switch models via environment variables (no code changes required):
#   LLM_MODE=auto|gemini|groq|local|mock   (auto = fastest available; best for demos)
#   LLM_MODEL_FAMILY=qwen|llama              (local mode only)
#   LLM_MODEL_SIZE=small|medium|large        (local mode only)
#   LLM_MODEL_NAME=<huggingface model>       (local mode only)
#   GEMINI_API_KEY=                          (free: https://aistudio.google.com/apikey)
#   GEMINI_MODEL=gemini-2.0-flash            (fast default)
#   GROQ_API_KEY=                            (free: https://console.groq.com)
#   GROQ_MODEL=llama-3.1-8b-instant
#   HF_TOKEN=<token>                         (required for gated Llama models)

MODEL_FAMILIES = {
    "qwen": {
        "small": "Qwen/Qwen2.5-0.5B-Instruct",
        "medium": "Qwen/Qwen2.5-1.5B-Instruct",
        "large": "Qwen/Qwen2.5-7B-Instruct",
    },
    "llama": {
        "small": "meta-llama/Llama-3-8b-Instruct",
        "medium": "meta-llama/Llama-3-8b-Instruct",
        "large": "meta-llama/Llama-3-8b-Instruct",
    },
}

HF_TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant").strip()

# Keep backward compatibility
MODEL_SIZES = MODEL_FAMILIES["qwen"]

class SystemDiagnostics:
    @staticmethod
    def profile():
        cuda_avail = torch.cuda.is_available()
        cuda_devices = torch.cuda.device_count() if cuda_avail else 0
        total_ram_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)
        
        logger.info(f"System Profiler: CUDA Available = {cuda_avail} ({cuda_devices} device(s)), Total RAM = {total_ram_gb} GB")
        
        # Decide configuration defaults
        if cuda_avail:
            default_mode = "local"
            default_size = "large"
        else:
            default_mode = "auto"  # Prefer cloud APIs on CPU; avoids slow local downloads
            if total_ram_gb > 16.0:
                default_size = "medium"
            else:
                default_size = "small"
                
        return {
            "cuda_available": cuda_avail,
            "cuda_device_count": cuda_devices,
            "ram_gb": total_ram_gb,
            "default_mode": default_mode,
            "default_size": default_size
        }

# Profile hardware on startup
diagnostics = SystemDiagnostics.profile()

# Load env variables with profiled defaults
LLM_MODE = os.environ.get("LLM_MODE", "gemini").lower()
LLM_MODEL_SIZE = os.environ.get("LLM_MODEL_SIZE", diagnostics["default_size"]).lower()

# Support model family selection (qwen or llama)
LLM_MODEL_FAMILY = os.environ.get("LLM_MODEL_FAMILY", "qwen").lower()
if LLM_MODEL_FAMILY not in MODEL_FAMILIES:
    logger.warning(f"Unknown model family '{LLM_MODEL_FAMILY}'. Defaulting to 'qwen'.")
    LLM_MODEL_FAMILY = "qwen"

# Get model name based on family and size
selected_family_models = MODEL_FAMILIES.get(LLM_MODEL_FAMILY, MODEL_FAMILIES["qwen"])
default_model_for_size = selected_family_models.get(LLM_MODEL_SIZE, selected_family_models.get("small", MODEL_SIZES.get(LLM_MODEL_SIZE, "Qwen/Qwen2.5-0.5B-Instruct")))

# Allow explicit override
LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", default_model_for_size)


def _resolve_llm_mode() -> str:
    """Pick the active backend. `auto` prefers fast cloud APIs for demos."""
    mode = LLM_MODE
    if mode != "auto":
        return mode
        if GEMINI_API_KEY:
            return "gemini"
        if GROQ_API_KEY:
            return "groq"
        if diagnostics["cuda_available"]:
            return "local"
        return "gemini" # Force gemini if mock is disabled


logger.info(
    f"LLM Configuration: MODE={LLM_MODE}, RESOLVED={_resolve_llm_mode()}, "
    f"FAMILY={LLM_MODEL_FAMILY}, SIZE={LLM_MODEL_SIZE}, MODEL_NAME={LLM_MODEL_NAME}"
)

class SentenceEmbeddingEngine:
    def __init__(self):
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer
            # Try to load the lightweight model
            logger.info("Initializing SentenceTransformer: all-MiniLM-L6-v2")
            self.model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
            logger.info("SentenceTransformer loaded successfully.")
        except Exception as e:
            logger.error(f"Could not load SentenceTransformer: {e}")
            raise RuntimeError(f"SentenceTransformer failed: {e}")

    def get_embedding(self, text: str) -> bytes:
        try:
            embedding = self.model.encode(text)
            return np.array(embedding, dtype=np.float32).tobytes()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise

    def compute_similarity(self, emb_a: bytes, emb_b: bytes) -> float:
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

# Initialize Embedding Engine
embedding_engine = SentenceEmbeddingEngine()

def _hf_auth_kwargs():
    return {"token": HF_TOKEN} if HF_TOKEN else {}


def _build_chat_prompt(system_prompt: str, user_prompt: str) -> tuple[str, str]:
    """Return (prompt, assistant_marker) for the active model family."""
    if LLM_MODEL_FAMILY == "llama":
        prompt = (
            f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
            f"{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
            f"{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        )
        return prompt, "<|start_header_id|>assistant<|end_header_id|>"

    prompt = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    return prompt, "<|im_start|>assistant\n"


class LocalLLMClient:
    def __init__(self):
        self.pipeline = None
        self.loaded = False
        
    def _lazy_load(self):
        if self.loaded:
            return
        try:
            from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
            auth = _hf_auth_kwargs()
            device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.float16 if device == "cuda" else torch.float32
            logger.info(f"Loading HF model: {LLM_MODEL_NAME} on {device}...")

            tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME, **auth)
            model = AutoModelForCausalLM.from_pretrained(
                LLM_MODEL_NAME,
                torch_dtype=dtype,
                low_cpu_mem_usage=True,
                **auth,
            )
            if device == "cuda":
                model = model.to(device)

            self.pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512,
                temperature=0.2,
                do_sample=True,
                device=0 if device == "cuda" else -1,
            )
            self.loaded = True
            logger.info(f"Model {LLM_MODEL_NAME} loaded successfully on {device}.")
        except Exception as e:
            logger.error(f"Failed to load HF local model {LLM_MODEL_NAME}: {e}. Falling back to Mock LLM.")
            self.loaded = False

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self._lazy_load()
        if not self.loaded or not self.pipeline:
            raise RuntimeError("Local pipeline not available.")
            
        try:
            prompt, assistant_marker = _build_chat_prompt(system_prompt, user_prompt)
            res = self.pipeline(prompt)
            output = res[0]["generated_text"]
            assistant_reply = output.split(assistant_marker)[-1]
            for stop in ("<|im_end|>", "<|eot_id|>"):
                assistant_reply = assistant_reply.split(stop)[0]
            return assistant_reply.strip()
        except Exception as e:
            logger.error(f"Generation error in LocalLLMClient: {e}")
            raise RuntimeError(f"Generation error in LocalLLMClient: {e}")

class GeminiLLMClient:
    """Google Gemini API — free tier, fast (~1-3s). Get key: https://aistudio.google.com/apikey"""
    
    def __init__(self):
        import httpx
        self.client = httpx.Client(timeout=90.0)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set. Cannot run without API key.")
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


class GroqLLMClient:
    """Groq API — free tier, very fast inference. Get key: https://console.groq.com"""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set. Cannot run without API key.")
        try:
            import httpx
            with httpx.Client(timeout=90.0) as client:
                res = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": GROQ_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.2,
                        "max_tokens": 2048,
                    },
                )
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise RuntimeError(f"Groq API error: {e}")

class MockLLMClient:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        cleaned_user = user_prompt.strip()
        combined_prompt = system_prompt + "\n" + cleaned_user
        
        # Adaptive reflection (life-focused, mood-aware)
        if "personal life stories" in system_prompt.lower() or "warm, thoughtful companion" in system_prompt.lower():
            return self._generate_adaptive_reflection(combined_prompt)

        # Check if this is a multiple story extraction request
        if "analyze the complete reflection journal and extract multiple independent, distinct story cards" in system_prompt.lower() or "story cards" in system_prompt.lower():
            return self._extract_multiple_stories(combined_prompt)

        # Legacy batch reflection prompts
        if "generate 4 personalized" in system_prompt.lower() or "reflection prompts" in system_prompt.lower():
            return self._generate_reflection_prompts(combined_prompt)
            
        # Check if this is a draft polishing request
        if "polish" in system_prompt.lower() or "draft sections" in system_prompt.lower():
            return self._polish_assembled_post(combined_prompt)
            
        # Check if this is Agent 1 Memory Extraction
        if "Agent 1" in system_prompt:
            return self._extract_memory(cleaned_user)
            
        # Check if this is Agent 2 question formulation or opportunity structuring
        if "Agent 2" in system_prompt or "Creative Strategy" in system_prompt or "storytelling" in system_prompt.lower():
            if "opportunity" in system_prompt.lower() or "structure the opportunity" in system_prompt.lower() or "content_type" in system_prompt.lower():
                return self._structure_opportunity(combined_prompt)
            else:
                return self._generate_strategy_chat_response(combined_prompt)
                
        # Generic fallback
        if "memory_type" in system_prompt or "structured memory" in system_prompt.lower():
            return self._extract_memory(cleaned_user)
            
        return "I'm not sure how to process this command. Please refine."

    def _generate_adaptive_reflection(self, combined_prompt: str) -> str:
        """Life-focused opener or mood-aware follow-up based on prior answers."""
        lower = combined_prompt.lower()

        if "follow-up question" in lower or "conversation so far" in lower:
            mood = "reflective"
            for m in ["happy", "emotional", "motivated", "nostalgic", "funny", "uncertain"]:
                if f"vibe so far: {m}" in lower or f"detected vibe so far: {m}" in lower:
                    mood = m
                    break
            for m, keywords in {
                "emotional": ["cry", "sad", "hurt", "miss", "anxious"],
                "happy": ["happy", "grateful", "excited", "laugh"],
                "motivated": ["motivated", "driven", "goal"],
                "nostalgic": ["remember", "childhood", "used to"],
            }.items():
                if any(k in lower for k in keywords):
                    mood = m
                    break

            # Pull a snippet from the user's answer for personalization
            answer_match = re.search(r"A:\s*(.{20,120})", combined_prompt)
            snippet = answer_match.group(1).strip() if answer_match else "that moment"

            if "follow-up question #2" in lower or '"id": "p2"' in lower:
                prompt = {
                    "detectedMood": mood,
                    "prompt": {
                        "id": "p2",
                        "sectionTitle": "The moment",
                        "title": f"What was going through your mind when {snippet[:60].rstrip('.')}…?",
                        "hint": "Try to recall one specific detail — a place, a face, a sound.",
                    },
                }
            else:
                prompt = {
                    "detectedMood": mood,
                    "prompt": {
                        "id": "p3",
                        "sectionTitle": "What shifted",
                        "title": "What feels different for you now, even in a small way?",
                        "hint": "It might be how you see someone, yourself, or what you want next.",
                    },
                }
            return json.dumps(prompt, indent=2)

        return json.dumps({
            "prompt": {
                "id": "p1",
                "sectionTitle": "Checking in",
                "title": "What's been on your heart lately?",
                "hint": "Could be something small — a text you reread, a walk, a feeling you can't shake.",
            }
        }, indent=2)

    def _generate_reflection_prompts(self, combined_prompt: str) -> str:
        """
        Legacy helper: life-focused reflection questions (fallback batch mode).
        """
        prompts = [
            {"id": "p1", "sectionTitle": "Checking in", "title": "What's been sitting with you lately?", "hint": "A feeling, a conversation, a moment you keep replaying."},
            {"id": "p2", "sectionTitle": "The moment", "title": "Can you walk me through the exact moment it hit you?", "hint": "Where were you? What did you see or hear?"},
            {"id": "p3", "sectionTitle": "What shifted", "title": "What changed for you after that — even if it was subtle?", "hint": "A belief, a feeling, a decision."},
        ]
        return json.dumps(prompts, indent=2)

    def _polish_assembled_post(self, combined_prompt: str) -> str:
        """
        Agent 2 Helper: Polishes raw draft sections into a highly engaging, trendy social media post
        with appropriate hooks, spacing, formatting, and emojis using trendy knowledge templates.
        """
        # Parse the sections from the prompt if possible
        hook_match = re.search(r'\[HOOK\]:\s*(.*)', combined_prompt, re.IGNORECASE)
        exp_match = re.search(r'\[EXPERIENCE\]:\s*(.*)', combined_prompt, re.IGNORECASE)
        conflict_match = re.search(r'\[CONFLICT\]:\s*(.*)', combined_prompt, re.IGNORECASE)
        lesson_match = re.search(r'\[LESSON\]:\s*(.*)', combined_prompt, re.IGNORECASE)
        cta_match = re.search(r'\[CTA\]:\s*(.*)', combined_prompt, re.IGNORECASE)
        
        hook = hook_match.group(1).strip() if hook_match else ""
        experience = exp_match.group(1).strip() if exp_match else ""
        conflict = conflict_match.group(1).strip() if conflict_match else ""
        lesson = lesson_match.group(1).strip() if lesson_match else ""
        cta = cta_match.group(1).strip() if cta_match else ""
        
        # Clean up tags or next line matches
        def clean_line(text):
            return text.split("[")[0].strip()
            
        hook = clean_line(hook)
        experience = clean_line(experience)
        conflict = clean_line(conflict)
        lesson = clean_line(lesson)
        cta = clean_line(cta)
        
        # Default fallback values if empty
        if not hook:
            hook = "I prepared for everything except the moment things actually broke."
        if not experience:
            experience = "We launched our first product beta last week. Within minutes, the server crashed under load."
        if not conflict:
            conflict = "Customers were complaining. My team was panicking. I wanted to disappear."
        if not lesson:
            lesson = "But then we realized: early users care about responsiveness, not perfection. We communicated openly, fixed the bug, and saved the day."
        if not cta:
            cta = "What's the hardest bug you shipped on a launch day?"

        # Format with premium, trendy layout (inspired by April 2026 deadpan, big font letter, and POV format trends)
        polished = (
            f"🔥 {hook}\n\n"
            f"📍 The Story:\n"
            f"{experience}\n\n"
            f"⚡ The Conflict:\n"
            f"↳ {conflict}\n\n"
            f"💡 The Hard Lesson:\n"
            f"• {lesson}\n\n"
            f"💬 Next Action:\n"
            f"{cta}"
        )
        return polished

    def _extract_memory(self, user_input: str) -> str:
        """
        Simulates Agent 1: Creator Memory Engine
        Extracts topics, turning points, emotions, content angles, traits from user reflection inputs.
        """
        # Remove LLM prompts or instruction wrappers if they leak in
        user_input_clean = re.sub(r'^extract structured memory from this text:\s*', '', user_input, flags=re.IGNORECASE)
        user_input_clean = re.sub(r'^extract structured memory from:\s*', '', user_input_clean, flags=re.IGNORECASE)
        
        text = user_input_clean.lower().strip()
        
        # 1. Smarter Topic Extraction with backward compatibility
        topics = []
        if any(w in text for w in ["college", "semester", "university", "engineering", "coding", "exam", "professor", "hackathon"]):
            topics.append("college")
        if any(w in text for w in ["engineer", "developer", "coding", "software", "bug", "hackathon", "build"]):
            topics.append("engineering")
        if any(w in text for w in ["job", "interview", "internship", "career", "manager", "hired", "rejected"]):
            topics.append("career")
        if any(w in text for w in ["founder", "startup", "company", "product", "users", "shipping", "saas"]):
            topics.append("startup")
        if any(w in text for w in ["quit", "resigned", "left", "walking away", "give up"]):
            topics.append("life_choices")
            
        if not topics:
            # Fall back to tech words matching or dynamic noun extraction
            tech_words = ["work", "office", "team", "story", "writing", "blog", "post", "video", "creator", "youtube", "design", "ui", "ux", "marketing", "sales"]
            for w in tech_words:
                if re.search(r'\b' + w + r'\b', text):
                    topics.append(w)
            if not topics:
                words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', text) if w not in ["with", "this", "that", "from", "have", "they", "them", "about", "what", "went"]]
                topics = words[:2] if words else ["growth"]
            
        # 2. Dynamic Turning Point Extraction
        turning_point = None
        tp_match = re.search(r'\b(but|then|finally|realized|learned|so|decided to|started|later|joining|changed)\b\s*(.*)', user_input_clean, re.IGNORECASE)
        if tp_match:
            turning_point = tp_match.group(2).strip()
            # Clean up trailing punctuation
            turning_point = re.sub(r'[.,!?]+$', '', turning_point)
            
        # 3. Dynamic Event Extraction
        # Default to the clean version of the sentence up to the turning point trigger
        event_part = user_input_clean
        if tp_match:
            event_part = user_input_clean[:tp_match.start()].strip()
            
        # Remove leading pronouns or time frames
        clean_event = re.sub(r'^(i|we|today i|today we|yesterday i|yesterday we|this week i|this week we|i think|i believe|i had to)\s+', '', event_part, flags=re.IGNORECASE)
        clean_event = re.sub(r'[.,!?]+$', '', clean_event).strip()
        # Capitalize first letter
        clean_event = clean_event[0].upper() + clean_event[1:] if clean_event else "reflection"
        
        # 4. Smarter Emotion Extraction
        emotions = []
        emo_map = {
            "uncertainty": ["struggle", "stuck", "frustrated", "hard", "insecure", "confused", "lost", "worry", "difficult"],
            "burnout": ["tired", "exhausted", "burnout", "overwhelmed", "stressed", "fatigue"],
            "accomplishment": ["happy", "excited", "win", "shipped", "proud", "great", "launch", "finished", "completed"],
            "vulnerability": ["fear", "anxious", "scared", "rejection", "failed", "doubt", "fraud", "imposter"],
            "clarity": ["realized", "learned", "peace", "clear", "nature", "walk", "understand"]
        }
        for emo, keywords in emo_map.items():
            if any(re.search(r'\b' + kw + r'\b', text) for kw in keywords):
                emotions.append(emo)
        if not emotions:
            emotions = ["reflection"]
            
        # Determine Memory Type
        mem_type = "personal_experience"
        if any(w in text for w in ["learned", "realized", "lesson", "realise"]):
            mem_type = "lesson"
        elif any(w in text for w in ["think", "believe", "opinion", "should"]):
            mem_type = "opinion"
            
        # Output angles
        angles = []
        for t in topics[:2]:
            angles.append(f"{t} struggles")
            angles.append(f"lessons from my {t} journey")
        angles.append("overcoming obstacles")
        
        result = {
            "memory_type": mem_type,
            "topic": topics[:3],
            "event": clean_event,
            "turning_point": turning_point,
            "emotion": emotions,
            "potential_content_angles": angles[:3],
            "creator_traits": {
                "likes_storytelling": True,
                "preferred_tone": "casual",
                "avoid_style": ["generic motivation", "guru advice"]
            }
        }
        
        return json.dumps(result, indent=2)

    def _structure_opportunity(self, conversation_history_str: str) -> str:
        """
        Agent 2 Helper: Generates final JSON opportunity when questioning is done.
        """
        history = conversation_history_str.lower()
        
        # Try to parse memory variables from history prompt
        event_match = re.search(r'active memory event:\s*([^\n\.]*)', conversation_history_str, re.IGNORECASE)
        tp_match = re.search(r'active memory turning point:\s*([^\n\.]*)', conversation_history_str, re.IGNORECASE)
        emotions_match = re.search(r'active memory emotions:\s*([^\n\.]*)', conversation_history_str, re.IGNORECASE)
        topics_match = re.search(r'active memory topics:\s*([^\n\.]*)', conversation_history_str, re.IGNORECASE)
        
        event = event_match.group(1).strip() if event_match else "your experience"
        turning_point = tp_match.group(1).strip() if tp_match else "a breakthrough moment"
        emotions = emotions_match.group(1).strip() if emotions_match else "insecurity"
        topics_str = topics_match.group(1).strip() if topics_match else "personal growth"
        topics = [t.strip() for t in topics_str.split(",") if t.strip()]
        if not topics:
            topics = ["creator_journey"]
 
        # Parse user answers if possible to extract hook ideas
        user_replies = [line.split(":")[-1].strip() for line in conversation_history_str.split("\n") if line.strip().startswith("User:") or line.strip().startswith("Creator:")]
        
        # Build dynamic topic
        tp_lower = str(turning_point).lower().strip()
        if "college" in history and "engineering" in history and "hackathon" in history:
            topic = "college insecurity to engineering passion"
        elif tp_lower and tp_lower not in ["none", "none mentioned", "null", ""]:
            # Clean up turning point formatting
            tp_clean = str(turning_point).strip()
            tp_clean = re.sub(r'^(it was|that|to|i|we|my|just|only|about|how|why)\s+', '', tp_clean, flags=re.IGNORECASE)
            tp_clean = tp_clean[0].lower() + tp_clean[1:] if tp_clean else "reflection"
            
            evt_clean = str(event).strip()
            evt_clean = evt_clean[0].lower() + evt_clean[1:] if evt_clean else "challenges"
            
            topic = f"How {tp_clean} helped me overcome {evt_clean}"
        else:
            evt_clean = str(event).strip()
            evt_clean = evt_clean[0].lower() + evt_clean[1:] if evt_clean else "my challenges"
            topic = f"Lessons from my experience with {evt_clean}"
            
        topic = topic.replace("  ", " ").strip()
        
        # Construct dynamic hooks based on user replies
        hooks = []
        if len(user_replies) > 0:
            hooks.append(f"I prepared for everything except the moment I had to face: {user_replies[0][:60]}...")
        else:
            hooks.append(f"I prepared for everything except the moment I had to face: {event}.")
            
        if tp_lower and tp_lower not in ["none", "none mentioned", "null", ""]:
            hooks.append(f"If you feel {emotions} in your {topics[0]} journey, read this. Here is what changed: {turning_point}.")
        else:
            hooks.append(f"If you feel {emotions} in your {topics[0]} journey, read this.")
            
        if len(user_replies) > 2:
            hooks.append(f"I learned this the hard way: {user_replies[2][:70]}...")
        else:
            hooks.append(f"A quiet lesson about {topics[0]} that took me months to realize.")
            
        # Check user answers specifically by stripping out the system prompt context to avoid matching system schema options
        user_text = ""
        for line in conversation_history_str.split("\n"):
            line_lower = line.strip().lower()
            if line_lower.startswith("user:") or line_lower.startswith("creator:") or line_lower.startswith("raw text context:") or line_lower.startswith("message:"):
                user_text += line + "\n"
        if not user_text:
            # Look at part after system prompt
            parts = conversation_history_str.split("system\n")
            user_text = parts[-1] if len(parts) > 1 else conversation_history_str
            
        user_text = user_text.lower()
        content_type = "story_reel"
        if "linkedin" in user_text or "post" in user_text:
            content_type = "linkedin_post"
        elif "newsletter" in user_text or "essay" in user_text:
            content_type = "newsletter"
            
        result = {
            "content_type": content_type,
            "topic": topic,
            "hook_options": hooks,
            "structure": ["context", "problem", "realization", "lesson"],
            "creator_inputs_used": [event] + ([turning_point] if tp_lower not in ["none", "none mentioned", "null", ""] else []) + topics
        }
        
        return json.dumps(result, indent=2)

    def _generate_strategy_chat_response(self, prompt: str) -> str:
        """
        Agent 2: Creative Strategy Agent chat messaging responses.
        Based on number of user answers in prompt, asks next questions or concludes.
        """
        # Count user replies in prompt history to track state
        history_lines = prompt.split("\n")
        user_replies = [line for line in history_lines if line.strip().lower().startswith("user:") or line.strip().lower().startswith("creator:")]
        reply_count = len(user_replies)
        
        # Extract memory variables from system prompt (passed as context)
        event_match = re.search(r'active memory event:\s*([^\n\.]*)', prompt, re.IGNORECASE)
        tp_match = re.search(r'active memory turning point:\s*([^\n\.]*)', prompt, re.IGNORECASE)
        emotions_match = re.search(r'active memory emotions:\s*([^\n\.]*)', prompt, re.IGNORECASE)
        topics_match = re.search(r'active memory topics:\s*([^\n\.]*)', prompt, re.IGNORECASE)
        
        event = event_match.group(1).strip() if event_match else "your experience"
        turning_point = tp_match.group(1).strip() if tp_match else "None"
        emotions = emotions_match.group(1).strip() if emotions_match else "growth"
        topics = topics_match.group(1).strip() if topics_match else "personal growth"
            
        if reply_count == 0:
            intro = f"I've retrieved your memory about **'{event}'**"
            if emotions and emotions != "None":
                intro += f" (where you experienced **{emotions}**)"
            intro += " and matched it with the storytelling framework.\n\n"
            
            return (
                f"{intro}Let's explore it together. First, tell me:\n"
                f"**What exactly happened during that event? What was the moment of peak tension or frustration?**"
            )
        elif reply_count == 1:
            last_ans = user_replies[-1].split(":")[-1].strip()
            last_ans = last_ans.replace('"', '').replace("'", "")
            truncated_ans = last_ans[:50] + "..." if len(last_ans) > 50 else last_ans
            
            turning_phrase = f"your turning point of '{turning_point}'" if turning_point and turning_point != "None" else "what changed"
            return (
                f"That makes sense. The tension in \"{truncated_ans}\" is exactly where the story builds.\n\n"
                f"Second question:\n"
                f"**What did you realize or do differently afterwards? What was the turning point (like {turning_phrase}) that changed your perspective?**"
            )
        elif reply_count == 2:
            return (
                f"I love that realization. The pivot is the core lesson of the piece.\n\n"
                "One final question before I structure this content opportunity:\n"
                f"**What advice would you give to someone else who is currently dealing with {event} or similar {topics} challenges?**"
            )
        else:
            return (
                "Excellent! I have everything I need to shape this story. "
                "Let's package this into a structured content opportunity now. "
                "[Opportunity Card Generated below]"
            )

    def _extract_multiple_stories(self, combined_prompt: str) -> str:
        """
        Agent 1 Helper: Mock story card extractor for a complete journal.
        """
        lower = combined_prompt.lower()
        stories = []
        if "internship" in lower or "rejection" in lower:
            stories = [
                {
                    "title": "Internship Rejection",
                    "summary": "Handling the sting of rejection from a dream internship and processing the emotional weight.",
                    "lesson": "A rejection is just a redirection to a path where you are truly valued.",
                    "emotion": "Vulnerability",
                    "category": "Career",
                    "tags": ["career", "rejection", "growth"]
                },
                {
                    "title": "Parents' Support",
                    "summary": "Realizing the depth of parental love and support when things didn't go as planned.",
                    "lesson": "Success is temporary, but the family that supports your struggle is permanent.",
                    "emotion": "Joy",
                    "category": "Relationships",
                    "tags": ["family", "support", "gratitude"]
                },
                {
                    "title": "Learning from Failure",
                    "summary": "Rebuilding confidence and strategy after failing to secure the expected role.",
                    "lesson": "Failure is the best training ground for resilience and self-reflection.",
                    "emotion": "Growth",
                    "category": "Mindset",
                    "tags": ["mindset", "failure", "learning"]
                }
            ]
        else:
            stories = [
                {
                    "title": "Overcoming Obstacles",
                    "summary": "Navigating recent life lessons and challenges that felt heavy at first.",
                    "lesson": "Quiet consistency compounds into clarity over time.",
                    "emotion": "Reflective",
                    "category": "Journey",
                    "tags": ["growth", "resilience"]
                },
                {
                    "title": "Finding Support",
                    "summary": "Revisiting conversations or support systems that helped ease the burden.",
                    "lesson": "You don't have to carry every transition alone.",
                    "emotion": "Grateful",
                    "category": "Relationships",
                    "tags": ["support", "connection"]
                }
            ]
        return json.dumps({"stories": stories}, indent=2)

# Instantiate LLM Clients
local_llm_client = LocalLLMClient()
gemini_llm_client = GeminiLLMClient()
groq_llm_client = GroqLLMClient()
mock_llm_client = MockLLMClient()

_LLM_CLIENTS = {
    "gemini": gemini_llm_client,
    "groq": groq_llm_client,
    "local": local_llm_client,
    "mock": mock_llm_client,
}


def get_llm():
    mode = _resolve_llm_mode()
    client = _LLM_CLIENTS.get(mode)
    if not client:
        raise ValueError(f"Unknown LLM_MODE '{LLM_MODE}'.")
    return client
