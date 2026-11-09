import os
os.environ["DSP_DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["DSP_SECRET_KEY"] = "test-secret-key-that-is-long-enough"

import asyncio
import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.main import app
from app.models import LearningModule, LearningTask, LearningTopic, LearningTrack, Skill
from app.core.rate_limit import clear_limits

engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
def database():
    clear_limits()
    Base.metadata.create_all(engine)
    with TestingSession() as db:
        skill = Skill(slug="statistics", name="Statistics", description="Statistical reasoning")
        track = LearningTrack(slug="statistics", title="Statistics", description="Statistics track", position=1)
        db.add_all([skill, track]); db.flush()
        module = LearningModule(track_id=track.id, title="Inference", description="Inference", position=1); db.add(module); db.flush()
        topic = LearningTopic(module_id=module.id, title="Testing", description="Testing", position=1); db.add(topic); db.flush()
        tasks = [
            LearningTask(topic_id=topic.id, title="Review inference", description="Review", objectives=["Explain"], duration_minutes=20, difficulty=2, task_type="theory", practical_exercise="Review examples", completion_criteria="Written notes", priority=60, skills=[skill]),
            LearningTask(topic_id=topic.id, title="Solve a test", description="Practice", objectives=["Apply"], duration_minutes=25, difficulty=3, task_type="practice", practical_exercise="Solve", completion_criteria="Correct solution", priority=80, skills=[skill]),
            LearningTask(topic_id=topic.id, title="Long project", description="Project", objectives=["Build"], duration_minutes=180, difficulty=4, task_type="project", practical_exercise="Build", completion_criteria="Report", priority=90, skills=[skill]),
        ]
        db.add_all(tasks); db.commit()
    yield
    Base.metadata.drop_all(engine)


async def override_db():
    with TestingSession() as db: yield db

app.dependency_overrides[get_db] = override_db


class ASGIClient:
    """Synchronous facade over HTTPX ASGI transport; preserves auth cookies."""
    def __init__(self): self.cookies = httpx.Cookies()
    def request(self, method: str, path: str, **kwargs):
        async def send():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", cookies=self.cookies) as client:
                response = await client.request(method, path, **kwargs)
                if "max-age=0" in response.headers.get("set-cookie", "").lower():
                    self.cookies.delete("access_token")
                else:
                    self.cookies.update(response.cookies)
                return response
        return asyncio.run(send())
    def get(self, path, **kwargs): return self.request("GET", path, **kwargs)
    def post(self, path, **kwargs): return self.request("POST", path, **kwargs)
    def put(self, path, **kwargs): return self.request("PUT", path, **kwargs)
    def patch(self, path, **kwargs): return self.request("PATCH", path, **kwargs)
    def delete(self, path, **kwargs): return self.request("DELETE", path, **kwargs)


@pytest.fixture
def client(): return ASGIClient()


@pytest.fixture
def authenticated(client):
    response = client.post("/api/auth/register", json={"email":"learner@example.com","password":"a-secure-password","display_name":"Ada"})
    assert response.status_code == 201
    return client
