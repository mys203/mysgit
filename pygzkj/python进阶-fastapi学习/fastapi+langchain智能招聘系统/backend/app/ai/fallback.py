from __future__ import annotations

import re
from typing import Any

from app.schemas.ai import GeneratedQuestion, ResumeParsedData

KNOWN_SKILLS = [
    "Python",
    "FastAPI",
    "Django",
    "Flask",
    "SQL",
    "MySQL",
    "PostgreSQL",
    "Redis",
    "Docker",
    "Kubernetes",
    "Java",
    "Go",
    "Vue",
    "React",
    "TypeScript",
    "JavaScript",
    "LangChain",
    "机器学习",
    "深度学习",
    "数据分析",
    "项目管理",
    "招聘",
]


def _first(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip(" ：:，,;；")
    return None


def parse_resume_locally(text: str) -> ResumeParsedData:
    normalized = text.replace("\r\n", "\n")
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    email = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", normalized)
    phone = re.search(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)", normalized)
    name = _first([r"^(?:姓名|名字)[：:]\s*(.+)$"], normalized)
    if not name and lines and len(lines[0]) <= 20 and "@" not in lines[0]:
        name = lines[0]
    education = _first([r"^(?:学历|最高学历)[：:]\s*(.+)$", r"(博士|硕士|本科|大专|高中)"], normalized)
    company = _first([r"^(?:公司|当前公司|现公司)[：:]\s*(.+)$"], normalized)
    title = _first([r"^(?:职位|岗位|当前职位|求职意向)[：:]\s*(.+)$"], normalized)
    years_text = _first([r"^(?:工作经验|工作年限|经验)[：:]\s*(\d+(?:\.\d+)?)\s*年?"], normalized)
    skills = [skill for skill in KNOWN_SKILLS if skill.lower() in normalized.lower()]
    summary = "；".join(lines[:12])[:800] if lines else None
    populated = sum(value is not None and value != [] for value in (name, email, phone, education, company, title, skills))
    return ResumeParsedData(
        name=name,
        email=email.group(0) if email else None,
        phone=phone.group(0) if phone else None,
        education=education,
        work_years=float(years_text) if years_text else None,
        current_company=company,
        current_title=title,
        skills=skills,
        summary=summary,
        confidence=min(0.9, 0.25 + populated * 0.1),
    )


def rule_match(job: dict[str, Any], candidate: dict[str, Any]) -> tuple[float, list[str]]:
    job_skills = {str(item).lower() for item in job.get("skills") or []}
    candidate_skills = {str(item).lower() for item in candidate.get("skills") or []}
    matched = sorted(job_skills & candidate_skills)
    missing = sorted(job_skills - candidate_skills)
    skill_score = 70.0 if not job_skills else 70.0 * len(matched) / len(job_skills)
    years = float(candidate.get("work_years") or 0)
    experience_score = min(12.0, years * 2.4)
    title = str(candidate.get("current_title") or "").lower()
    job_title = str(job.get("title") or "").lower()
    title_score = 10.0 if title and (title in job_title or job_title in title) else 0.0
    requirements = str(job.get("requirements") or "").lower()
    summary = f"{candidate.get('summary') or ''} {candidate.get('education') or ''}".lower()
    hits = sum(1 for token in re.findall(r"[\w一-鿿]{2,}", requirements) if token in summary)
    keyword_score = min(8.0, hits * 1.0)
    score = min(100.0, round(skill_score + experience_score + title_score + keyword_score, 2))
    reasons: list[str] = []
    if matched:
        reasons.append(f"命中技能：{', '.join(matched)}")
    if missing:
        reasons.append(f"缺少技能：{', '.join(missing[:8])}")
    reasons.append(f"相关工作年限：{years:g} 年")
    if title_score:
        reasons.append("当前职位与目标岗位方向接近")
    if keyword_score:
        reasons.append("简历经历与岗位要求存在关键词重合")
    return score, reasons


def generate_questions_locally(
    job: dict[str, Any],
    candidate: dict[str, Any] | None,
    count: int,
    categories: list[str],
) -> list[GeneratedQuestion]:
    title = job.get("title") or "目标岗位"
    skills = list(job.get("skills") or [])
    name = (candidate or {}).get("name") or "候选人"
    templates = [
        (categories[0], f"请结合项目说明你如何使用 {skills[0] if skills else title} 解决具体业务问题？", "关注背景、选型、个人职责和量化结果。"),
        (categories[min(1, len(categories) - 1)], "请讲述一次复杂问题定位过程，你如何验证根因并防止复发？", "使用 STAR 结构，关注分析过程和实际贡献。"),
        (categories[min(2, len(categories) - 1)], f"如果入职 {title}，你会如何设计第一个月目标和验证方式？", "关注目标拆解、优先级、风险和度量指标。"),
        (categories[0], f"请解释你在 {', '.join(skills[:3]) if skills else '核心技能'} 方面的熟练程度并给出证据。", "通过案例区分了解、使用和独立设计。"),
        (categories[min(1, len(categories) - 1)], f"{name} 在资源不足时如何推动团队交付结果？", "关注沟通、取舍和结果意识。"),
    ]
    return [
        GeneratedQuestion(question=q, category=c, reference_answer=a, score_weight=1.0)
        for c, q, a in (templates * ((count + 4) // 5))[:count]
    ]


def answer_chat_locally(
    question: str,
    sources: list[dict[str, Any]],
    *,
    no_context_message: bool = False,
) -> str:
    if no_context_message:
        return (
            "当前没有关联业务资料，我只能基于你的问题提供通用建议。"
            "请先切换岗位或候选人上下文，再询问具体的人岗匹配、简历或面试信息。"
        )
    if sources:
        labels = "、".join(f"[S{item['index']}]" for item in sources[:5])
        return (
            f"已读取当前会话关联的业务资料（{labels}）。"
            "AI 服务当前未启用或暂时降级，无法生成进一步分析；"
            "你可以查看引用资料，或稍后重试本次问答。"
        )
    return (
        "AI 服务当前未启用或暂时降级。"
        "我可以基于你提供的问题给出通用建议，但不会虚构岗位、候选人或面试数据。"
    )


def chat_injection_response() -> str:
    return (
        "检测到输入中可能包含提示词注入或越权指令。"
        "该内容不会被执行，也不会泄露系统提示词或内部配置；"
        "请改为询问岗位、候选人、简历、匹配结论或面试题相关内容。"
    )
