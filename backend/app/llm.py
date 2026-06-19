import os
import re
import json
import logging
import datetime
import numpy as np
import torch
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("creatoros.llm")

# Model Maps
MODEL_SIZES = {
    "small": "Qwen/Qwen2.5-0.5B-Instruct",
    "medium": "Qwen/Qwen2.5-1.5B-Instruct",
    "large": "Qwen/Qwen2.5-7B-Instruct"
}

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
            default_mode = "mock"  # Start in mock by default to avoid downloading big models automatically
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
LLM_MODE = os.environ.get("LLM_MODE", diagnostics["default_mode"]).lower()
LLM_MODEL_SIZE = os.environ.get("LLM_MODEL_SIZE", diagnostics["default_size"]).lower()
LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", MODEL_SIZES.get(LLM_MODEL_SIZE, "Qwen/Qwen2.5-0.5B-Instruct"))

logger.info(f"LLM Configuration: MODE={LLM_MODE}, SIZE={LLM_MODEL_SIZE}, MODEL_NAME={LLM_MODEL_NAME}")

class SentenceEmbeddingEngine:
    def __init__(self):
        self.model = None
        self.offline_fallback = False
        if LLM_MODE == "mock":
            logger.info("LLM_MODE is 'mock'. Skipping SentenceTransformer initialization and enabling offline fallback.")
            self.offline_fallback = True
            return
        try:
            from sentence_transformers import SentenceTransformer
            # Try to load the lightweight model
            logger.info("Initializing SentenceTransformer: all-MiniLM-L6-v2")
            self.model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
            logger.info("SentenceTransformer loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer: {e}. Falling back to simple keyword matching embeddings.")
            self.offline_fallback = True

    def get_embedding(self, text: str) -> bytes:
        if self.offline_fallback or not self.model:
            # Simple hash-based fallback or mock array of length 384
            # We seed based on word frequencies
            words = re.findall(r'\w+', text.lower())
            arr = np.zeros(384, dtype=np.float32)
            for w in words:
                idx = sum(ord(c) for c in w) % 384
                arr[idx] += 1.0
            norm = np.linalg.norm(arr)
            if norm > 0:
                arr = arr / norm
            return arr.tobytes()
        try:
            embedding = self.model.encode(text)
            return np.array(embedding, dtype=np.float32).tobytes()
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            arr = np.zeros(384, dtype=np.float32).tobytes()
            return arr

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

class LocalLLMClient:
    def __init__(self):
        self.pipeline = None
        self.loaded = False
        
    def _lazy_load(self):
        if self.loaded:
            return
        try:
            from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
            logger.info(f"Loading HF model: {LLM_MODEL_NAME} on CPU...")
            
            # Using CPU, float32, low memory usage settings
            tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
            model = AutoModelForCausalLM.from_pretrained(
                LLM_MODEL_NAME, 
                torch_dtype=torch.float32, 
                low_cpu_mem_usage=True
            )
            
            self.pipeline = pipeline(
                "text-generation", 
                model=model, 
                tokenizer=tokenizer,
                max_new_tokens=512,
                temperature=0.2,
                do_sample=True
            )
            self.loaded = True
            logger.info(f"Model {LLM_MODEL_NAME} loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load HF local model {LLM_MODEL_NAME}: {e}. Falling back to Mock LLM.")
            self.loaded = False

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self._lazy_load()
        if not self.loaded or not self.pipeline:
            # Fallback to mock
            logger.warning("Local pipeline not available. Falling back to Mock generator.")
            return mock_llm_client.generate(system_prompt, user_prompt)
            
        try:
            prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
            res = self.pipeline(prompt)
            output = res[0]['generated_text']
            # Extract assistant's reply
            assistant_reply = output.split("<|im_start|>assistant\n")[-1].replace("<|im_end|>", "").strip()
            return assistant_reply
        except Exception as e:
            logger.error(f"Generation error in LocalLLMClient: {e}")
            return mock_llm_client.generate(system_prompt, user_prompt)

class MockLLMClient:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Simulates Agent 1 JSON memory extraction or Agent 2 questioning system
        based on keyword rules, regex parsing, and template generation.
        """
        cleaned_user = user_prompt.strip()
        combined_prompt = system_prompt + "\n" + cleaned_user
        
        # Check if this is a prompts generation request
        if "generate 6 personalized" in system_prompt.lower() or "reflection prompts" in system_prompt.lower():
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

    def _generate_reflection_prompts(self, combined_prompt: str) -> str:
        """
        Agent 1 Helper: Generates 6 personalized reflection questions based on niche and interests.
        """
        # Default fallback prompts
        prompts = [
            {"id": "p1", "title": "What was the biggest technical hurdle you faced this week?", "hint": "Describe the bug, system architecture problem, or design issue."},
            {"id": "p2", "title": "Did you have an opinion shift about any coding practices or tools?", "hint": "A framework you used to love but now dislike, or vice-versa."},
            {"id": "p3", "title": "What did you ship or deploy, and how did the initial feedback feel?", "hint": "A feature launch, pull request merge, or demo video show."},
            {"id": "p4", "title": "Where did you feel out of your depth or experience imposter syndrome?", "hint": "A conversation with a senior engineer or a design review session."},
            {"id": "p5", "title": "Who gave you a piece of unexpected technical or product advice?", "hint": "A coworker, a tweet, a github issue, or a blog post."},
            {"id": "p6", "title": "If you could write one warning to your past self this week, what would it be?", "hint": "Save others from making the same mistake by sharing the lesson."}
        ]
        
        lower_prompt = combined_prompt.lower()
        if "storytelling" in lower_prompt or "writing" in lower_prompt:
            prompts[0] = {"id": "p1", "title": "What storytelling hook caught your eye this week?", "hint": "A hook from a newsletter, a LinkedIn post, or a book chapter."}
            prompts[3] = {"id": "p4", "title": "Where did you struggle to find the right voice or structure?", "hint": "A draft you rewrote three times or a pitch that fell flat."}
            prompts[5] = {"id": "p6", "title": "What authentic lesson from your creative journey is worth sharing now?", "hint": "An experience where being transparent built trust with your readers."}
            
        if "startup" in lower_prompt or "founder" in lower_prompt:
            prompts[1] = {"id": "p2", "title": "What did you learn from a user interacting with your product?", "hint": "A bug report, a screen recording, or a feature request interview."}
            prompts[2] = {"id": "p3", "title": "What was your biggest win in user growth or product shipping?", "hint": "A customer conversion, a product launch milestone, or a successful demo."}
            prompts[4] = {"id": "p5", "title": "What founder burnout signal did you notice or manage this week?", "hint": "A day you wanted to close the laptop or a realization about pacing."}
            
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

# Instantiate LLM Clients
mock_llm_client = MockLLMClient()
local_llm_client = LocalLLMClient()

def get_llm():
    if LLM_MODE == "local":
        return local_llm_client
    return mock_llm_client
