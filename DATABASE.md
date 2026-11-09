# Database

PostgreSQL is the source of truth. User-owned records are never stored only in the browser; local storage contains only the recoverable active-timer pointer.

## Main relationships

```text
LearningTrack → LearningModule → LearningTopic → LearningTask
LearningTask ↔ prerequisite LearningTask
LearningTask ↔ Skill

User → UserTaskProgress → LearningTask
User → StudySession → LearningTask
User → UserSkillAssessment → Skill
User → UserProjectProgress → LearningProject → ProjectMilestone
User → Reflection → optional Task / Project
User → RecommendationHistory
User → UserPreferences
```

Curriculum entities have stable IDs, active flags, and version fields. Revision creates a new task/version and retires the old one instead of deleting it, so historic progress and sessions continue to resolve.

Unique constraints prevent duplicate user/task, user/skill, and user/project records. Indexes cover email lookup, task hierarchy foreign keys, user session/history access, and progress state queries. PostgreSQL owns timestamps where possible.

## Migrations

```bash
cd apps/api
.venv/bin/alembic upgrade head
.venv/bin/alembic revision --autogenerate -m "describe change"
.venv/bin/alembic downgrade -1  # development only, inspect first
```

Review generated migrations before committing. Apply migrations before starting a newly deployed API revision.

## Backup and restore

Create a provider-independent logical backup at least weekly and before migrations:

```bash
pg_dump --format=custom --no-owner "$DATABASE_URL" > dsp-$(date +%F).dump
pg_restore --clean --if-exists --no-owner --dbname "$RESTORE_DATABASE_URL" dsp-YYYY-MM-DD.dump
```

Test restoration quarterly into a separate database. The in-product JSON export is for user portability; it is not a substitute for a full relational backup.

## Account deletion

After identity verification and a final export, delete the `users` row in a transaction. User-owned tables use `ON DELETE CASCADE`; shared curriculum, resources, and projects remain. Log only a non-sensitive deletion audit identifier outside the user database if operational policy requires it.

