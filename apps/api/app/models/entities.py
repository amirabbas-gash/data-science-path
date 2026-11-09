from __future__ import annotations
from datetime import date, datetime
from enum import StrEnum
from typing import Any
from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ProgressState(StrEnum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    needs_review = "needs_review"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(120))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LearningTrack(Base):
    __tablename__ = "learning_tracks"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(default=0)
    version: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(default=True)
    modules: Mapped[list[LearningModule]] = relationship(back_populates="track", order_by="LearningModule.position")


class LearningModule(Base):
    __tablename__ = "learning_modules"
    id: Mapped[int] = mapped_column(primary_key=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("learning_tracks.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(default=0)
    track: Mapped[LearningTrack] = relationship(back_populates="modules")
    topics: Mapped[list[LearningTopic]] = relationship(back_populates="module", order_by="LearningTopic.position")


class LearningTopic(Base):
    __tablename__ = "learning_topics"
    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("learning_modules.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(default=0)
    module: Mapped[LearningModule] = relationship(back_populates="topics")
    tasks: Mapped[list[LearningTask]] = relationship(back_populates="topic", order_by="LearningTask.position")


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)


task_skills = __import__("sqlalchemy").Table(
    "task_skills", Base.metadata,
    __import__("sqlalchemy").Column("task_id", ForeignKey("learning_tasks.id"), primary_key=True),
    __import__("sqlalchemy").Column("skill_id", ForeignKey("skills.id"), primary_key=True),
)


class LearningTask(Base):
    __tablename__ = "learning_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("learning_topics.id"), index=True)
    title: Mapped[str] = mapped_column(String(220))
    description: Mapped[str] = mapped_column(Text)
    objectives: Mapped[list[str]] = mapped_column(JSON, default=list)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    difficulty: Mapped[int] = mapped_column(Integer)
    task_type: Mapped[str] = mapped_column(String(30), default="practice")
    practical_exercise: Mapped[str] = mapped_column(Text)
    completion_criteria: Mapped[str] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(default=50)
    position: Mapped[int] = mapped_column(default=0)
    version: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(default=True)
    topic: Mapped[LearningTopic] = relationship(back_populates="tasks")
    skills: Mapped[list[Skill]] = relationship(secondary=task_skills)
    prerequisites: Mapped[list[LearningTask]] = relationship(
        secondary="task_prerequisites", primaryjoin="LearningTask.id==TaskPrerequisite.task_id",
        secondaryjoin="LearningTask.id==TaskPrerequisite.prerequisite_id", viewonly=True,
    )


class TaskPrerequisite(Base):
    __tablename__ = "task_prerequisites"
    task_id: Mapped[int] = mapped_column(ForeignKey("learning_tasks.id"), primary_key=True)
    prerequisite_id: Mapped[int] = mapped_column(ForeignKey("learning_tasks.id"), primary_key=True)


class UserTaskProgress(Base):
    __tablename__ = "user_task_progress"
    __table_args__ = (UniqueConstraint("user_id", "task_id"), Index("ix_progress_user_state", "user_id", "state"))
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("learning_tasks.id"), index=True)
    state: Mapped[ProgressState] = mapped_column(Enum(ProgressState), default=ProgressState.not_started)
    completion_percent: Mapped[int] = mapped_column(default=0)
    confidence: Mapped[int | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    task: Mapped[LearningTask] = relationship()


class UserSkillAssessment(Base):
    __tablename__ = "user_skill_assessments"
    __table_args__ = (UniqueConstraint("user_id", "skill_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    self_level: Mapped[int] = mapped_column(default=1)
    demonstrated_level: Mapped[float] = mapped_column(Float, default=1.0)
    confidence: Mapped[int] = mapped_column(default=3)
    evidence_count: Mapped[int] = mapped_column(default=0)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    skill: Mapped[Skill] = relationship()


class StudySession(Base):
    __tablename__ = "study_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("learning_tasks.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(20), default="active")
    notes: Mapped[str] = mapped_column(Text, default="")
    learned: Mapped[str] = mapped_column(Text, default="")
    difficulties: Mapped[str] = mapped_column(Text, default="")
    difficulty_rating: Mapped[int | None] = mapped_column(nullable=True)
    confidence_rating: Mapped[int | None] = mapped_column(nullable=True)
    needs_practice: Mapped[bool] = mapped_column(default=False)
    task: Mapped[LearningTask | None] = relationship()


class LearningProject(Base):
    __tablename__ = "learning_projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    objectives: Mapped[list[str]] = mapped_column(JSON, default=list)
    dataset_url: Mapped[str] = mapped_column(String(500), default="")
    skill_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    position: Mapped[int] = mapped_column(default=0)
    milestones: Mapped[list[ProjectMilestone]] = relationship(back_populates="project", order_by="ProjectMilestone.position")


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("learning_projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    completion_criteria: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(default=0)
    project: Mapped[LearningProject] = relationship(back_populates="milestones")


class UserProjectProgress(Base):
    __tablename__ = "user_project_progress"
    __table_args__ = (UniqueConstraint("user_id", "project_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[int] = mapped_column(ForeignKey("learning_projects.id"))
    completed_milestone_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    github_url: Mapped[str] = mapped_column(String(500), default="")
    results: Mapped[str] = mapped_column(Text, default="")
    reflection: Mapped[str] = mapped_column(Text, default="")


class LearningResource(Base):
    __tablename__ = "learning_resources"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(220))
    url: Mapped[str] = mapped_column(String(500))
    resource_type: Mapped[str] = mapped_column(String(30))
    topic: Mapped[str] = mapped_column(String(120))
    difficulty: Mapped[int] = mapped_column(default=2)
    description: Mapped[str] = mapped_column(Text)


class Reflection(Base):
    __tablename__ = "reflections"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("learning_tasks.id"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("learning_projects.id"), nullable=True)
    entry_date: Mapped[date] = mapped_column(Date, default=date.today)
    topic: Mapped[str] = mapped_column(String(160))
    learned: Mapped[str] = mapped_column(Text)
    difficulties: Mapped[str] = mapped_column(Text, default="")
    questions: Mapped[str] = mapped_column(Text, default="")
    next_steps: Mapped[str] = mapped_column(Text, default="")


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    preferred_topics: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_durations: Mapped[list[int]] = mapped_column(JSON, default=lambda: [30, 60, 90])
    default_study_minutes: Mapped[int] = mapped_column(default=60)


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    available_minutes: Mapped[int] = mapped_column(Integer)
    task_ids: Mapped[list[int]] = mapped_column(JSON)
    explanations: Mapped[dict[str, Any]] = mapped_column(JSON)
    accepted_task_id: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

