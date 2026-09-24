from __future__ import annotations

import secrets
import time

from fastapi.testclient import TestClient

from tests.conftest import TEST_PASSWORD


def wait_for_task(client: TestClient, headers: dict[str, str], task_no: str) -> dict:
    for _ in range(50):
        response = client.get(f"/api/v1/ai/tasks/{task_no}", headers=headers)
        assert response.status_code == 200, response.text
        task = response.json()["data"]
        if task["status"] in {"SUCCEEDED", "FAILED"}:
            assert task["status"] == "SUCCEEDED", task
            return task
        time.sleep(0.05)
    raise AssertionError(f"AI 任务未完成：{task_no}")


def test_login_refresh_me_and_logout(client: TestClient):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": TEST_PASSWORD},
    )
    assert login.status_code == 200
    body = login.json()
    assert body["code"] == 0
    assert body["request_id"]
    tokens = body["data"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert "ADMIN" in me.json()["data"]["roles"]

    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()["data"]
    assert new_tokens["access_token"] != tokens["access_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        json={"refresh_token": new_tokens["refresh_token"]},
    )
    assert logout.status_code == 200


def test_job_lifecycle_and_rbac(client: TestClient, auth_headers: dict[str, str]):
    created = client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={
            "title": "Python 后端工程师",
            "code": "JOB-PY-001",
            "description": "负责招聘系统后端",
            "requirements": "熟悉 Python、FastAPI、SQL、Redis",
            "skills": ["Python", "FastAPI", "SQL", "Redis"],
            "headcount": 1,
        },
    )
    assert created.status_code == 201, created.text
    job_id = created.json()["data"]["id"]

    published = client.post(f"/api/v1/jobs/{job_id}/publish", headers=auth_headers)
    assert published.status_code == 200
    assert published.json()["data"]["status"] == "PUBLISHED"

    listing = client.get("/api/v1/jobs?page=1&page_size=10", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["data"]["total"] >= 1

    viewer_password = secrets.token_urlsafe(18)
    user = client.post(
        "/api/v1/users",
        headers=auth_headers,
        json={
            "username": "viewer01",
            "password": viewer_password,
            "real_name": "只读用户",
            "role_codes": ["VIEWER"],
        },
    )
    assert user.status_code == 201, user.text
    viewer_login = client.post(
        "/api/v1/auth/login",
        json={"username": "viewer01", "password": viewer_password},
    )
    viewer_headers = {
        "Authorization": f"Bearer {viewer_login.json()['data']['access_token']}"
    }
    denied = client.post(
        "/api/v1/jobs",
        headers=viewer_headers,
        json={"title": "越权岗位", "code": "JOB-DENIED"},
    )
    assert denied.status_code == 403


def test_resume_upload_parse_confirm_candidate_application(
    client: TestClient, auth_headers: dict[str, str]
):
    job = client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={
            "title": "FastAPI 开发",
            "code": "JOB-PY-002",
            "requirements": "Python FastAPI Redis",
            "skills": ["Python", "FastAPI", "Redis"],
        },
    )
    assert job.status_code == 201
    job_id = job.json()["data"]["id"]

    resume_text = (
        "姓名：张三\n"
        "邮箱：zhangsan@example.com\n"
        "手机：13800138000\n"
        "学历：本科\n"
        "工作经验：5年\n"
        "当前公司：示例科技\n"
        "当前职位：Python 后端工程师\n"
        "技能：Python FastAPI SQL Redis LangChain"
    )
    uploaded = client.post(
        "/api/v1/resumes/upload",
        headers=auth_headers,
        files={"file": ("zhangsan.txt", resume_text.encode("utf-8"), "text/plain")},
    )
    assert uploaded.status_code == 201, uploaded.text
    resume_id = uploaded.json()["data"]["id"]

    duplicate = client.post(
        "/api/v1/resumes/upload",
        headers=auth_headers,
        files={"file": ("zhangsan-copy.txt", resume_text.encode("utf-8"), "text/plain")},
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["data"]["duplicated"] is True
    assert "file_path" not in duplicate.json()["data"]
    assert "raw_text" not in duplicate.json()["data"]

    parsed = client.post(f"/api/v1/resumes/{resume_id}/parse", headers=auth_headers)
    assert parsed.status_code == 202, parsed.text
    parsed_data = parsed.json()["data"]
    wait_for_task(client, auth_headers, parsed_data["task_no"])
    record_id = parsed_data["parse_record"]["id"]
    parse_record = client.get(
        f"/api/v1/parse-records/{record_id}", headers=auth_headers
    )
    assert parse_record.status_code == 200
    assert parse_record.json()["data"]["status"] == "PARSED"

    confirmed = client.post(
        f"/api/v1/parse-records/{record_id}/confirm",
        headers=auth_headers,
        json={"job_position_id": job_id},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["data"]["candidate_id"]
    assert confirmed.json()["data"]["application_id"]


def test_candidate_ai_match_and_interview_questions(
    client: TestClient, auth_headers: dict[str, str]
):
    job = client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={
            "title": "AI 平台工程师",
            "code": "JOB-AI-001",
            "requirements": "Python LangChain Redis 向量检索",
            "skills": ["Python", "LangChain", "Redis"],
        },
    )
    job_id = job.json()["data"]["id"]

    candidate = client.post(
        "/api/v1/candidates",
        headers=auth_headers,
        json={
            "name": "李四",
            "email": "lisi@example.com",
            "phone": "13900139000",
            "work_years": 4,
            "current_title": "AI 平台工程师",
            "skills": ["Python", "LangChain", "Redis"],
            "summary": "负责 RAG 和招聘智能化项目",
        },
    )
    assert candidate.status_code == 201, candidate.text
    candidate_id = candidate.json()["data"]["id"]

    match = client.post(
        "/api/v1/ai/matches",
        headers=auth_headers,
        json={"job_id": job_id, "candidate_ids": [candidate_id], "top_k": 10},
    )
    assert match.status_code == 202, match.text
    match_task = wait_for_task(client, auth_headers, match.json()["data"]["task_no"])
    assert match_task["degraded"] is True
    assert match_task["output_payload"]["items"][0]["score"] > 0
    match_result_id = match_task["output_payload"]["items"][0]["id"]
    assert (
        client.get(
            f"/api/v1/match-results/{match_result_id}", headers=auth_headers
        ).status_code
        == 200
    )

    questions = client.post(
        "/api/v1/ai/interview-questions",
        headers=auth_headers,
        json={
            "job_id": job_id,
            "candidate_id": candidate_id,
            "count": 3,
            "categories": ["专业知识", "项目经历"],
        },
    )
    assert questions.status_code == 202, questions.text
    question_task = wait_for_task(
        client, auth_headers, questions.json()["data"]["task_no"]
    )
    listed = client.get(
        "/api/v1/interview-questions?status=DRAFT&page=1&page_size=10",
        headers=auth_headers,
    )
    assert listed.status_code == 200, listed.text
    question_items = listed.json()["data"]["items"]
    assert len(question_items) == 3
    approved = client.post(
        "/api/v1/interview-questions/approve",
        headers=auth_headers,
        json={"question_ids": [item["id"] for item in question_items]},
    )
    assert approved.status_code == 200
    assert approved.json()["data"]["approved_count"] == 3


def test_interview_and_dashboard(client: TestClient, auth_headers: dict[str, str]):
    job = client.post(
        "/api/v1/jobs",
        headers=auth_headers,
        json={"title": "面试测试岗位", "code": "JOB-INT-001"},
    )
    job_id = job.json()["data"]["id"]
    candidate = client.post(
        "/api/v1/candidates",
        headers=auth_headers,
        json={"name": "王五", "email": "wangwu@example.com"},
    )
    candidate_id = candidate.json()["data"]["id"]
    created = client.post(
        "/api/v1/interviews",
        headers=auth_headers,
        json={
            "job_id": job_id,
            "candidate_id": candidate_id,
            "title": "后端一面",
            "scheduled_at": "2026-10-01T02:00:00Z",
        },
    )
    assert created.status_code == 201, created.text
    interview_id = created.json()["data"]["id"]
    assert client.get(f"/api/v1/interviews/{interview_id}", headers=auth_headers).status_code == 200

    generated = client.post(
        "/api/v1/ai/interview-questions",
        headers=auth_headers,
        json={
            "job_id": job_id,
            "candidate_id": candidate_id,
            "interview_id": interview_id,
            "count": 2,
            "categories": ["专业知识"],
        },
    )
    assert generated.status_code == 202
    wait_for_task(client, auth_headers, generated.json()["data"]["task_no"])
    scoped = client.get(
        f"/api/v1/interviews/{interview_id}/questions", headers=auth_headers
    )
    assert scoped.status_code == 200
    assert len(scoped.json()["data"]["items"]) == 2
    global_questions = client.get(
        "/api/v1/interview-questions?status=DRAFT&category=专业知识&page=1&page_size=20",
        headers=auth_headers,
    )
    assert global_questions.status_code == 200
    assert global_questions.json()["data"]["total"] >= 2

    summary = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert summary.status_code == 200
    assert "jobs" in summary.json()["data"]
