from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMModel):
    id: int
    email: EmailStr
    display_name: str
    timezone: str


class SkillOut(ORMModel):
    id: int
    slug: str
    name: str


class TaskOut(ORMModel):
    id: int
    title: str
    description: str
    objectives: list[str]
    duration_minutes: int
    difficulty: int
    task_type: str
    practical_exercise: str
    completion_criteria: str
    skills: list[SkillOut] = []


class ProgressUpdate(BaseModel):
    state: str
    completion_percent: int = Field(ge=0, le=100)
    confidence: int | None = Field(default=None, ge=1, le=5)


class SessionCreate(BaseModel):
    task_id: int | None = None
    started_at: datetime | None = None
    duration_minutes: int = Field(default=0, ge=0, le=1440)
    notes: str = ""


class SessionUpdate(BaseModel):
    action: str | None = None
    ended_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=0, le=1440)
    notes: str | None = None
    learned: str | None = None
    difficulties: str | None = None
    difficulty_rating: int | None = Field(default=None, ge=1, le=5)
    confidence_rating: int | None = Field(default=None, ge=1, le=5)
    needs_practice: bool | None = None


class SkillUpdate(BaseModel):
    self_level: int = Field(ge=1, le=5)
    confidence: int = Field(ge=1, le=5)


class ReflectionCreate(BaseModel):
    entry_date: date = Field(default_factory=date.today)
    topic: str = Field(min_length=1, max_length=160)
    learned: str = Field(min_length=1)
    difficulties: str = ""
    questions: str = ""
    next_steps: str = ""
    task_id: int | None = None
    project_id: int | None = None


class PreferencesUpdate(BaseModel):
    timezone: str | None = None
    preferred_topics: list[str] | None = None
    preferred_durations: list[int] | None = None
    default_study_minutes: int | None = Field(default=None, ge=15, le=600)


class AccountDelete(BaseModel):
    password: str
    confirmation: str
