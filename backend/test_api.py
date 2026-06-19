import os
import json
import unittest
import shutil

# Set environment variables for testing before imports
os.environ["LLM_MODE"] = "mock"
os.environ["DATABASE_URL"] = "sqlite:///./test_creatoros.db"

from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base

class TestCreatorOS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize test client context to trigger lifespans (and db init)
        cls.client_ctx = TestClient(app)
        cls.client = cls.client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls):
        # Exit context manager
        cls.client_ctx.__exit__(None, None, None)
        # Clean up test database files
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test_creatoros.db"):
            try:
                os.remove("./test_creatoros.db")
            except Exception:
                pass

    def test_01_workspace_initial(self):
        # Verify the home workspace endpoint returns initial mock states
        res = self.client.get("/api/workspace")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("continueReflection", data)
        self.assertIn("recentStories", data)
        self.assertIn("weeklyPlan", data)
        self.assertIn("balance", data)
        self.assertTrue(len(data["recentStories"]) > 0)

    def test_02_reflection_flow(self):
        # 1. Fetch active reflection session
        res = self.client.get("/api/reflections/active")
        self.assertEqual(res.status_code, 200)
        sess = res.json()
        session_id = sess["id"]
        prompts = sess["prompts"]
        self.assertTrue(len(prompts) > 0)

        # 2. Answer a prompt
        payload = {
            "promptId": "p1",
            "value": "I hated my first semester because everyone seemed ahead of me. Later joining a hackathon changed how I saw engineering."
        }
        res = self.client.post("/api/reflections/answer", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

        # 3. Complete reflection (triggers Agent 1 memory extraction pipeline)
        res = self.client.post(f"/api/reflections/complete/{session_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["storiesDiscovered"] >= 1)

        # 4. Check that memory timeline is populated
        res = self.client.get("/api/memories")
        self.assertEqual(res.status_code, 200)
        memories = res.json()
        self.assertTrue(len(memories) >= 1)
        self.assertEqual(memories[0]["memory_type"], "personal_experience")
        self.assertIn("college", memories[0]["topic"])
        self.assertIn("engineering", memories[0]["topic"])
        self.assertIn("hackathon", memories[0]["turning_point"].lower())

    def test_03_strategy_agent_chat_flow(self):
        # 1. Retrieve extracted memory from previous step
        res = self.client.get("/api/memories")
        self.assertEqual(res.status_code, 200)
        memory = res.json()[0]
        memory_id = memory["id"]

        # 2. Start a strategy chat linked to this memory
        res = self.client.post("/api/strategy/chat/sessions", json={"memoryId": memory_id})
        self.assertEqual(res.status_code, 200)
        session = res.json()
        session_id = session["id"]
        self.assertEqual(session["status"], "active")

        # 3. Fetch details, check the first agent question is seeded
        res = self.client.get(f"/api/strategy/chat/sessions/{session_id}")
        self.assertEqual(res.status_code, 200)
        details = res.json()
        self.assertTrue(len(details["messages"]) == 1)
        self.assertEqual(details["messages"][0]["role"], "assistant")
        self.assertIn("What exactly happened during this event?", details["messages"][0]["content"])

        # 4. Send response to Question 1 -> Expect Question 2
        res = self.client.post(
            f"/api/strategy/chat/sessions/{session_id}/message", 
            json={"message": "I struggled with coding initially and felt like a fraud."}
        )
        self.assertEqual(res.status_code, 200)
        reply1 = res.json()
        self.assertFalse(reply1["isCompleted"])
        self.assertEqual(reply1["message"]["role"], "assistant")
        self.assertIn("Second question:", reply1["message"]["content"])

        # 5. Send response to Question 2 -> Expect Question 3
        res = self.client.post(
            f"/api/strategy/chat/sessions/{session_id}/message", 
            json={"message": "In the hackathon, I helped build a working app in 48 hours and realized I can learn quickly."}
        )
        self.assertEqual(res.status_code, 200)
        reply2 = res.json()
        self.assertFalse(reply2["isCompleted"])
        self.assertIn("final question", reply2["message"]["content"])

        # 6. Send response to Question 3 -> Expect complete & structured opportunity
        res = self.client.post(
            f"/api/strategy/chat/sessions/{session_id}/message", 
            json={"message": "Don't judge your engineering career by the first 3 months. Find a practical project."}
        )
        self.assertEqual(res.status_code, 200)
        reply3 = res.json()
        self.assertTrue(reply3["isCompleted"])
        self.assertIn("structured this into a content opportunity", reply3["message"]["content"])
        self.assertIsNotNone(reply3["opportunity"])
        
        opp = reply3["opportunity"]
        self.assertEqual(opp["content_type"], "story_reel")
        self.assertEqual(opp["topic"], "college insecurity to engineering passion")
        self.assertTrue(len(opp["hook_options"]) > 0)
        self.assertIn("opportunity_id", opp)
        
        # 7. Check the Story Bank contains the new opportunity
        res = self.client.get("/api/stories")
        self.assertEqual(res.status_code, 200)
        stories = res.json()
        # Should have seeded dummy ones + the newly generated one
        self.assertTrue(len(stories) >= 3)
        new_story = next(s for s in stories if s["title"] == "college insecurity to engineering passion")
        self.assertEqual(new_story["status"], "idea")

        # 8. Check that Workspace draft is initialized for the story
        res = self.client.get(f"/api/stories/{new_story['id']}/draft")
        self.assertEqual(res.status_code, 200)
        draft = res.json()
        self.assertEqual(draft["storyId"], new_story["id"])
        self.assertIn("hook", draft["sections"])
        self.assertEqual(draft["sections"]["hook"], opp["hook_options"][0])

    def test_04_opportunity_feedback_loop(self):
        # 1. Find the newly created story
        res = self.client.get("/api/stories")
        self.assertEqual(res.status_code, 200)
        stories = res.json()
        target_story = next(s for s in stories if s["title"] == "college insecurity to engineering passion")
        story_id = target_story["id"]

        # 2. Post feedback to refine hooks
        res = self.client.post(
            f"/api/stories/{story_id}/feedback",
            json={"feedback": "make the hooks sound more casual and witty"}
        )
        self.assertEqual(res.status_code, 200)
        refined = res.json()
        self.assertTrue(refined["success"])
        self.assertTrue(len(refined["hook_options"]) > 0)

    def test_05_draft_preview_polish(self):
        # 1. Find the newly created story
        res = self.client.get("/api/stories")
        self.assertEqual(res.status_code, 200)
        stories = res.json()
        target_story = next(s for s in stories if s["title"] == "college insecurity to engineering passion")
        story_id = target_story["id"]

        # 2. Call preview endpoint with raw sections
        payload = {
            "sections": {
                "hook": "I felt like a fraud.",
                "experience": "My first semester in college was terrible.",
                "conflict": "Everyone seemed ahead of me.",
                "lesson": "I joined a hackathon and realized I can learn quickly.",
                "cta": "What was your turning point?"
            }
        }
        res = self.client.post(f"/api/stories/{story_id}/preview", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("polishedText", data)
        self.assertIn("🔥", data["polishedText"])
        self.assertIn("📍", data["polishedText"])
        self.assertIn("💡", data["polishedText"])

if __name__ == "__main__":
    unittest.main()
