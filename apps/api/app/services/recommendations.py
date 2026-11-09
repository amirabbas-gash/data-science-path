from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.models import LearningTask, ProgressState, StudySession, UserSkillAssessment, UserTaskProgress


@dataclass
class ScoredTask:
    task: LearningTask
    score: float
    reasons: list[str]


class DeterministicRecommendationEngine:
    """Explainable scoring followed by a duration-constrained, type-balanced plan."""

    def recommend(self, db: Session, user_id: int, available_minutes: int) -> list[ScoredTask]:
        tasks = db.scalars(
            select(LearningTask).where(LearningTask.is_active.is_(True)).options(
                selectinload(LearningTask.skills), selectinload(LearningTask.prerequisites)
            )
        ).all()
        progress = {p.task_id: p for p in db.scalars(select(UserTaskProgress).where(UserTaskProgress.user_id == user_id))}
        skill_levels = {a.skill_id: a for a in db.scalars(select(UserSkillAssessment).where(UserSkillAssessment.user_id == user_id))}
        recent_ids = set(db.scalars(select(StudySession.task_id).where(
            StudySession.user_id == user_id,
            StudySession.started_at >= datetime.now(timezone.utc) - timedelta(days=3),
        )))
        candidates: list[ScoredTask] = []
        for task in tasks:
            state = progress.get(task.id)
            if state and state.state == ProgressState.completed and state.confidence and state.confidence >= 4:
                continue
            if any(progress.get(pre.id) is None or progress[pre.id].state != ProgressState.completed for pre in task.prerequisites):
                continue
            if task.duration_minutes > available_minutes:
                continue
            score, reasons = task.priority / 10, []
            if state and state.state == ProgressState.in_progress:
                score += 8
                reasons.append("continues unfinished work")
            if state and (state.state == ProgressState.needs_review or (state.confidence or 5) <= 2):
                score += 7
                reasons.append("reinforces a low-confidence area")
            weak = [s.name for s in task.skills if s.id in skill_levels and skill_levels[s.id].demonstrated_level < 2.5]
            if weak:
                score += min(6, 2 * len(weak))
                reasons.append(f"builds evidence in {', '.join(weak[:2])}")
            fit = task.duration_minutes / available_minutes
            score += 4 * fit
            if fit >= .3:
                reasons.append("fits the available study window")
            if task.id in recent_ids:
                score -= 3
            if task.task_type in {"practice", "project"}:
                score += 2
                reasons.append("adds practical work")
            if not reasons:
                reasons.append("unlocks useful next steps in the roadmap")
            candidates.append(ScoredTask(task, score, reasons))
        candidates.sort(key=lambda item: (-item.score, item.task.duration_minutes))
        plan: list[ScoredTask] = []
        remaining = available_minutes
        used_types: set[str] = set()
        for item in candidates:
            diversity_bonus = 2 if item.task.task_type not in used_types else 0
            item.score += diversity_bonus
            if item.task.duration_minutes <= remaining:
                plan.append(item)
                remaining -= item.task.duration_minutes
                used_types.add(item.task.task_type)
            if remaining < 15 or len(plan) >= 6:
                break
        return plan

