from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_token, hash_password, verify_password
from app.core.rate_limit import limit_auth
from app.models import *
from app.schemas.api import *
from app.services.recommendations import DeterministicRecommendationEngine

router = APIRouter(prefix="/api")


@router.post("/auth/register", response_model=UserOut, status_code=201, dependencies=[Depends(limit_auth(5))])
async def register(request: Request, payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(func.lower(User.email) == payload.email.lower())):
        raise HTTPException(409, "Email already registered")
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password), display_name=payload.display_name)
    db.add(user); db.flush(); db.add(UserPreferences(user_id=user.id)); db.commit(); db.refresh(user)
    _set_cookie(response, user.id)
    return user


@router.post("/auth/login", response_model=UserOut, dependencies=[Depends(limit_auth(8))])
async def login(request: Request, payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(func.lower(User.email) == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    _set_cookie(response, user.id)
    return user


def _set_cookie(response: Response, user_id: int):
    response.set_cookie("access_token", create_token(user_id), httponly=True, secure=settings.secure_cookies,
                        samesite="lax", max_age=settings.access_token_minutes * 60, path="/")


@router.post("/auth/logout", status_code=204)
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")


@router.get("/auth/me", response_model=UserOut)
async def me(user: User = Depends(current_user)): return user


@router.get("/roadmap")
async def roadmap(user: User = Depends(current_user), db: Session = Depends(get_db)):
    tracks = db.scalars(select(LearningTrack).where(LearningTrack.is_active.is_(True)).order_by(LearningTrack.position).options(
        selectinload(LearningTrack.modules).selectinload(LearningModule.topics).selectinload(LearningTopic.tasks).selectinload(LearningTask.skills)
    )).all()
    progress = {p.task_id: p for p in db.scalars(select(UserTaskProgress).where(UserTaskProgress.user_id == user.id))}
    return [{"id": t.id, "title": t.title, "description": t.description, "modules": [
        {"id": m.id, "title": m.title, "description": m.description, "topics": [
            {"id": p.id, "title": p.title, "tasks": [TaskOut.model_validate(x).model_dump() | {
                "state": progress[x.id].state if x.id in progress else "not_started",
                "completion_percent": progress[x.id].completion_percent if x.id in progress else 0,
            } for x in p.tasks if x.is_active]} for p in m.topics]} for m in t.modules]} for t in tracks]


@router.put("/tasks/{task_id}/progress")
async def update_progress(task_id: int, payload: ProgressUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not db.get(LearningTask, task_id): raise HTTPException(404, "Task not found")
    item = db.scalar(select(UserTaskProgress).where(UserTaskProgress.user_id == user.id, UserTaskProgress.task_id == task_id))
    if not item: item = UserTaskProgress(user_id=user.id, task_id=task_id); db.add(item)
    try: item.state = ProgressState(payload.state)
    except ValueError: raise HTTPException(422, "Invalid progress state")
    item.completion_percent, item.confidence = payload.completion_percent, payload.confidence
    item.completed_at = datetime.now(timezone.utc) if item.state == ProgressState.completed else None
    db.commit(); return {"ok": True}


@router.get("/recommendations")
async def recommendations(minutes: int = Query(ge=15, le=600), user: User = Depends(current_user), db: Session = Depends(get_db)):
    plan = DeterministicRecommendationEngine().recommend(db, user.id, minutes)
    result = [{"task": TaskOut.model_validate(x.task), "score": round(x.score, 2), "explanation": "; ".join(x.reasons)} for x in plan]
    db.add(RecommendationHistory(user_id=user.id, available_minutes=minutes, task_ids=[x.task.id for x in plan], explanations={str(x.task.id): x.reasons for x in plan}))
    db.commit(); return {"available_minutes": minutes, "planned_minutes": sum(x.task.duration_minutes for x in plan), "items": result}


@router.post("/sessions", status_code=201)
async def create_session(payload: SessionCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if payload.task_id and not db.get(LearningTask, payload.task_id): raise HTTPException(404, "Task not found")
    item = StudySession(user_id=user.id, task_id=payload.task_id, started_at=payload.started_at or datetime.now(timezone.utc), duration_minutes=payload.duration_minutes, notes=payload.notes)
    db.add(item); db.commit(); db.refresh(item); return item


@router.patch("/sessions/{session_id}")
async def update_session(session_id: int, payload: SessionUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = db.scalar(select(StudySession).where(StudySession.id == session_id, StudySession.user_id == user.id))
    if not item: raise HTTPException(404, "Session not found")
    data = payload.model_dump(exclude_unset=True); action = data.pop("action", None)
    for key, value in data.items(): setattr(item, key, value)
    if action == "pause": item.status = "paused"
    elif action == "resume": item.status = "active"
    elif action == "complete":
        item.status = "completed"; item.ended_at = item.ended_at or datetime.now(timezone.utc)
        if not payload.duration_minutes: item.duration_minutes = max(1, int((item.ended_at - item.started_at).total_seconds() / 60))
    db.commit(); db.refresh(item); return item


@router.get("/sessions")
async def sessions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(StudySession).where(StudySession.user_id == user.id).order_by(StudySession.started_at.desc()).options(selectinload(StudySession.task))).all()


@router.get("/skills")
async def skills(user: User = Depends(current_user), db: Session = Depends(get_db)):
    assessments = {a.skill_id: a for a in db.scalars(select(UserSkillAssessment).where(UserSkillAssessment.user_id == user.id))}
    return [{"id": s.id, "slug": s.slug, "name": s.name, "description": s.description,
             "self_level": assessments[s.id].self_level if s.id in assessments else 1,
             "demonstrated_level": assessments[s.id].demonstrated_level if s.id in assessments else 1,
             "confidence": assessments[s.id].confidence if s.id in assessments else 3,
             "evidence_count": assessments[s.id].evidence_count if s.id in assessments else 0} for s in db.scalars(select(Skill).order_by(Skill.name))]


@router.put("/skills/{skill_id}")
async def update_skill(skill_id: int, payload: SkillUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not db.get(Skill, skill_id): raise HTTPException(404, "Skill not found")
    item = db.scalar(select(UserSkillAssessment).where(UserSkillAssessment.user_id == user.id, UserSkillAssessment.skill_id == skill_id))
    if not item: item = UserSkillAssessment(user_id=user.id, skill_id=skill_id); db.add(item)
    item.self_level, item.confidence, item.assessed_at = payload.self_level, payload.confidence, datetime.now(timezone.utc)
    db.commit(); return {"ok": True}


@router.get("/projects")
async def projects(user: User = Depends(current_user), db: Session = Depends(get_db)):
    progress = {x.project_id: x for x in db.scalars(select(UserProjectProgress).where(UserProjectProgress.user_id == user.id))}
    items = db.scalars(select(LearningProject).order_by(LearningProject.position).options(selectinload(LearningProject.milestones))).all()
    return [{"id": p.id, "slug": p.slug, "title": p.title, "description": p.description, "objectives": p.objectives,
             "dataset_url": p.dataset_url, "skill_tags": p.skill_tags, "milestones": p.milestones,
             "completed_milestone_ids": progress[p.id].completed_milestone_ids if p.id in progress else []} for p in items]


@router.put("/projects/{project_id}/milestones/{milestone_id}")
async def toggle_milestone(project_id: int, milestone_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    milestone = db.scalar(select(ProjectMilestone).where(ProjectMilestone.id == milestone_id, ProjectMilestone.project_id == project_id))
    if not milestone: raise HTTPException(404, "Milestone not found")
    item = db.scalar(select(UserProjectProgress).where(UserProjectProgress.user_id == user.id, UserProjectProgress.project_id == project_id))
    if not item: item = UserProjectProgress(user_id=user.id, project_id=project_id); db.add(item)
    ids = list(item.completed_milestone_ids or []); ids.remove(milestone_id) if milestone_id in ids else ids.append(milestone_id); item.completed_milestone_ids = ids
    db.commit(); return {"completed_milestone_ids": ids}


@router.get("/resources")
async def resources(topic: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(LearningResource).order_by(LearningResource.topic, LearningResource.title)
    if topic: query = query.where(LearningResource.topic == topic)
    return db.scalars(query).all()


@router.post("/reflections", status_code=201)
async def create_reflection(payload: ReflectionCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    item = Reflection(user_id=user.id, **payload.model_dump()); db.add(item); db.commit(); db.refresh(item); return item


@router.get("/reflections")
async def reflections(q: str = "", user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Reflection).where(Reflection.user_id == user.id)
    if q: query = query.where(or_(Reflection.topic.ilike(f"%{q}%"), Reflection.learned.ilike(f"%{q}%"), Reflection.difficulties.ilike(f"%{q}%"), Reflection.questions.ilike(f"%{q}%"), Reflection.next_steps.ilike(f"%{q}%")))
    return db.scalars(query.order_by(Reflection.entry_date.desc())).all()


@router.get("/dashboard")
async def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(LearningTask).where(LearningTask.is_active.is_(True))) or 0
    completed = db.scalar(select(func.count()).select_from(UserTaskProgress).where(UserTaskProgress.user_id == user.id, UserTaskProgress.state == ProgressState.completed)) or 0
    minutes = db.scalar(select(func.coalesce(func.sum(StudySession.duration_minutes), 0)).where(StudySession.user_id == user.id, StudySession.status == "completed")) or 0
    sessions_by_day = db.execute(select(func.date(StudySession.started_at), func.sum(StudySession.duration_minutes)).where(StudySession.user_id == user.id).group_by(func.date(StudySession.started_at)).order_by(func.date(StudySession.started_at).desc()).limit(14)).all()
    projects_total = db.scalar(select(func.count()).select_from(ProjectMilestone)) or 0
    projects_done = sum(len(x.completed_milestone_ids or []) for x in db.scalars(select(UserProjectProgress).where(UserProjectProgress.user_id == user.id)))
    return {"total_tasks": total, "completed_tasks": completed, "progress_percent": round(100 * completed / total) if total else 0,
            "learning_minutes": minutes, "project_milestones": {"completed": projects_done, "total": projects_total},
            "weekly_activity": [{"date": str(d), "minutes": int(m)} for d, m in reversed(sessions_by_day)]}


@router.get("/export")
async def export_data(user: User = Depends(current_user), db: Session = Depends(get_db)):
    def rows(model):
        return [{c.name: getattr(x, c.name) for c in model.__table__.columns if c.name not in {"password_hash"}} for x in db.scalars(select(model).where(model.user_id == user.id))]
    return {"schema_version": 1, "exported_at": datetime.now(timezone.utc), "profile": {"email": user.email, "display_name": user.display_name, "timezone": user.timezone},
            "task_progress": rows(UserTaskProgress), "study_sessions": rows(StudySession), "skill_assessments": rows(UserSkillAssessment),
            "project_progress": rows(UserProjectProgress), "reflections": rows(Reflection)}


@router.put("/settings")
async def update_settings(payload: PreferencesUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    prefs = db.get(UserPreferences, user.id) or UserPreferences(user_id=user.id); db.add(prefs)
    data = payload.model_dump(exclude_unset=True); timezone_name = data.pop("timezone", None)
    if timezone_name: user.timezone = timezone_name
    for k, v in data.items(): setattr(prefs, k, v)
    db.commit(); return {"ok": True}


@router.delete("/account", status_code=204)
async def delete_account(payload: AccountDelete, response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if payload.confirmation != "DELETE" or not verify_password(payload.password, user.password_hash):
        raise HTTPException(400, "Password or confirmation is incorrect")
    db.delete(user); db.commit(); response.delete_cookie("access_token", path="/")
