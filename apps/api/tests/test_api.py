from datetime import datetime, timezone


def test_authentication_and_protected_routes(client):
    assert client.get("/api/dashboard").status_code == 401
    created = client.post("/api/auth/register", json={"email":"me@example.com","password":"a-secure-password","display_name":"Learner"})
    assert created.status_code == 201
    assert created.json()["email"] == "me@example.com"
    assert client.get("/api/auth/me").status_code == 200
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/login", json={"email":"me@example.com","password":"wrong-password"}).status_code == 401


def test_duplicate_registration_is_rejected(authenticated):
    response = authenticated.post("/api/auth/register", json={"email":"learner@example.com","password":"a-secure-password","display_name":"Ada"})
    assert response.status_code == 409


def test_cross_origin_mutation_is_rejected(client):
    response = client.post(
        "/api/auth/register",
        headers={"Origin": "https://attacker.example"},
        json={"email":"me@example.com","password":"a-secure-password","display_name":"Learner"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Untrusted request origin"


def test_roadmap_and_progress_are_user_scoped(authenticated):
    roadmap = authenticated.get("/api/roadmap").json()
    task = roadmap[0]["modules"][0]["topics"][0]["tasks"][0]
    response = authenticated.put(f"/api/tasks/{task['id']}/progress", json={"state":"completed","completion_percent":100,"confidence":3})
    assert response.status_code == 200
    refreshed = authenticated.get("/api/roadmap").json()
    assert refreshed[0]["modules"][0]["topics"][0]["tasks"][0]["state"] == "completed"


def test_recommendations_fit_budget_and_explain_selection(authenticated):
    result = authenticated.get("/api/recommendations?minutes=60").json()
    assert result["planned_minutes"] <= 60
    assert result["items"]
    assert all(item["explanation"] for item in result["items"])
    assert all(item["task"]["duration_minutes"] <= 60 for item in result["items"])
    assert "Long project" not in [x["task"]["title"] for x in result["items"]]


def test_recommender_prioritizes_unfinished_work(authenticated):
    tasks = authenticated.get("/api/roadmap").json()[0]["modules"][0]["topics"][0]["tasks"]
    review = next(x for x in tasks if x["title"] == "Review inference")
    authenticated.put(f"/api/tasks/{review['id']}/progress", json={"state":"in_progress","completion_percent":40,"confidence":3})
    result = authenticated.get("/api/recommendations?minutes=60").json()
    selected = next(x for x in result["items"] if x["task"]["id"] == review["id"])
    assert "unfinished" in selected["explanation"]


def test_session_lifecycle_persists_reflection_fields(authenticated):
    task = authenticated.get("/api/roadmap").json()[0]["modules"][0]["topics"][0]["tasks"][0]
    created = authenticated.post("/api/sessions", json={"task_id":task["id"],"started_at":datetime.now(timezone.utc).isoformat()}).json()
    assert authenticated.patch(f"/api/sessions/{created['id']}", json={"action":"pause"}).json()["status"] == "paused"
    assert authenticated.patch(f"/api/sessions/{created['id']}", json={"action":"resume"}).json()["status"] == "active"
    done = authenticated.patch(f"/api/sessions/{created['id']}", json={"action":"complete","duration_minutes":32,"learned":"Tests connect estimands to decisions","difficulties":"Choosing assumptions","confidence_rating":3,"needs_practice":True}).json()
    assert done["status"] == "completed" and done["duration_minutes"] == 32 and done["needs_practice"] is True


def test_skill_assessment_does_not_inflate_demonstrated_level(authenticated):
    skill = authenticated.get("/api/skills").json()[0]
    authenticated.put(f"/api/skills/{skill['id']}", json={"self_level":5,"confidence":5})
    updated = authenticated.get("/api/skills").json()[0]
    assert updated["self_level"] == 5
    assert updated["demonstrated_level"] == 1


def test_reflection_search_and_export(authenticated):
    authenticated.post("/api/reflections", json={"topic":"Bootstrap intervals","learned":"Resampling estimates uncertainty","questions":"When does coverage fail?"})
    assert len(authenticated.get("/api/reflections?q=coverage").json()) == 1
    exported = authenticated.get("/api/export").json()
    assert exported["schema_version"] == 1
    assert exported["profile"]["email"] == "learner@example.com"
    assert len(exported["reflections"]) == 1


def test_project_milestone_toggle(authenticated):
    # Empty test fixture has no projects; endpoint should be safely scoped and return not found.
    assert authenticated.put("/api/projects/999/milestones/999").status_code == 404


def test_account_deletion_requires_password_and_confirmation(authenticated):
    assert authenticated.delete("/api/account", json={"password":"wrong-password","confirmation":"DELETE"}).status_code == 400
    assert authenticated.delete("/api/account", json={"password":"a-secure-password","confirmation":"DELETE"}).status_code == 204
    assert authenticated.get("/api/auth/me").status_code == 401
