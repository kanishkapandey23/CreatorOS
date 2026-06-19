import os
import json
import unittest

# Set environment variables for testing before imports
os.environ["LLM_MODE"] = "mock"
os.environ["DATABASE_URL"] = "sqlite:///./test_creatoros.db"

from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base


class TestCreatorOS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_ctx = TestClient(app)
        cls.client = cls.client_ctx.__enter__()
        res = cls.client.post(
            "/api/auth/register",
            json={
                "email": "test@creatoros.app",
                "password": "testpassword123",
                "name": "Test User",
            },
        )
        assert res.status_code == 200, res.text
        cls.auth_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

    @classmethod
    def tearDownClass(cls):
        cls.client_ctx.__exit__(None, None, None)
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test_creatoros.db"):
            try:
                os.remove("./test_creatoros.db")
            except Exception:
                pass

    def test_00_auth_required(self):
        res = self.client.get("/api/workspace")
        self.assertEqual(res.status_code, 401)

    def test_00b_auth_me(self):
        res = self.client.get("/api/auth/me", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["email"], "test@creatoros.app")

    def test_00c_oauth_providers(self):
        res = self.client.get("/api/auth/oauth/providers")
        self.assertEqual(res.status_code, 200)
        self.assertIn("providers", res.json())
        self.assertIsInstance(res.json()["providers"], list)

    def test_01_workspace_initial(self):
        res = self.client.get("/api/workspace", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("continueReflection", data)
        self.assertIn("recentStories", data)
        self.assertIn("weeklyPlan", data)
        self.assertIn("balance", data)
        self.assertTrue(len(data["recentStories"]) > 0)

    def test_02_reflection_flow(self):
        res = self.client.get("/api/reflections/active", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        sess = res.json()
        session_id = sess["id"]
        prompts = sess["prompts"]
        self.assertTrue(len(prompts) > 0)

        payload = {
            "promptId": "p1",
            "value": "I hated my first semester because everyone seemed ahead of me. Later joining a hackathon changed how I saw engineering."
        }
        res = self.client.post("/api/reflections/answer", json=payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

        res = self.client.post(f"/api/reflections/complete/{session_id}", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["storiesDiscovered"] >= 1)

        res = self.client.get("/api/memories", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        memories = res.json()
        self.assertTrue(len(memories) >= 1)
        self.assertEqual(memories[0]["memory_type"], "personal_experience")
        self.assertIn("college", memories[0]["topic"])
        self.assertIn("engineering", memories[0]["topic"])
        self.assertIn("hackathon", memories[0]["turning_point"].lower())

    def test_03_strategy_agent_chat_flow(self):
        res = self.client.get("/api/memories", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        memory = res.json()[0]
        memory_id = memory["id"]

        res = self.client.post("/api/strategy/chat/sessions", json={"memoryId": memory_id}, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        session = res.json()
        session_id = session["id"]
        self.assertEqual(session["status"], "active")

        res = self.client.get(f"/api/strategy/chat/sessions/{session_id}", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        details = res.json()
        self.assertTrue(len(details["messages"]) == 1)
        self.assertEqual(details["messages"][0]["role"], "assistant")
        self.assertIn("What exactly happened during this event?", details["messages"][0]["content"])

        res = self.client.post(
            f"/api/strategy/chat/sessions/{session_id}/message",
            json={"message": "I struggled with coding initially and felt like a fraud."},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)
        reply1 = res.json()
        self.assertFalse(reply1["isCompleted"])
        self.assertEqual(reply1["message"]["role"], "assistant")
        self.assertIn("Second question:", reply1["message"]["content"])

        res = self.client.post(
            f"/api/strategy/chat/sessions/{session_id}/message",
            json={"message": "In the hackathon, I helped build a working app in 48 hours and realized I can learn quickly."},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)
        reply2 = res.json()
        self.assertFalse(reply2["isCompleted"])
        self.assertIn("final question", reply2["message"]["content"])

        res = self.client.post(
            f"/api/strategy/chat/sessions/{session_id}/message",
            json={"message": "Don't judge your engineering career by the first 3 months. Find a practical project."},
            headers=self.auth_headers,
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

        res = self.client.get("/api/stories", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        stories = res.json()
        self.assertTrue(len(stories) >= 3)
        new_story = next(s for s in stories if s["title"] == "college insecurity to engineering passion")
        self.assertEqual(new_story["status"], "idea")

        res = self.client.get(f"/api/stories/{new_story['id']}/draft", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        draft = res.json()
        self.assertEqual(draft["storyId"], new_story["id"])
        self.assertIn("hook", draft["sections"])
        self.assertEqual(draft["sections"]["hook"], opp["hook_options"][0])

    def test_04_opportunity_feedback_loop(self):
        res = self.client.get("/api/stories", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        stories = res.json()
        target_story = next(s for s in stories if s["title"] == "college insecurity to engineering passion")
        story_id = target_story["id"]

        res = self.client.post(
            f"/api/stories/{story_id}/feedback",
            json={"feedback": "make the hooks sound more casual and witty"},
            headers=self.auth_headers,
        )
        self.assertEqual(res.status_code, 200)
        refined = res.json()
        self.assertTrue(refined["success"])
        self.assertTrue(len(refined["hook_options"]) > 0)

    def test_05_draft_preview_polish(self):
        res = self.client.get("/api/stories", headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        stories = res.json()
        target_story = next(s for s in stories if s["title"] == "college insecurity to engineering passion")
        story_id = target_story["id"]

        payload = {
            "sections": {
                "hook": "I felt like a fraud.",
                "experience": "My first semester in college was terrible.",
                "conflict": "Everyone seemed ahead of me.",
                "lesson": "I joined a hackathon and realized I can learn quickly.",
                "cta": "What was your turning point?"
            }
        }
        res = self.client.post(f"/api/stories/{story_id}/preview", json=payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("polishedText", data)
        self.assertIn("🔥", data["polishedText"])
        self.assertIn("📍", data["polishedText"])
        self.assertIn("💡", data["polishedText"])


if __name__ == "__main__":
    unittest.main()
