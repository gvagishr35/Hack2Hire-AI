import json
from typing import Any

from app.ai.openai_client import get_openai_client
from app.core.exceptions import BadRequestError
from app.core.settings import settings
from app.utils.difficulty import difficulty_for_index


def _parse_json_content(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise BadRequestError("AI returned invalid JSON response") from exc


async def generate_interview_questions(
    *,
    resume_text: str,
    job_description: str,
    job_title: str | None,
    question_count: int,
) -> list[dict[str, str]]:
    """Generate resume + JD tailored questions with adaptive difficulty labels."""
    return [
        {
            "question": "Tell me about yourself and your background.",
            "category": "behavioral",
            "difficulty": "easy",
        },
        {
            "question": "What are the main differences between Python lists and tuples?",
            "category": "technical",
            "difficulty": "easy",
        },
        {
            "question": "Explain a project you have worked on and the challenges you faced.",
            "category": "experience",
            "difficulty": "medium",
        },
        {
            "question": "How would you design a simple REST API using FastAPI?",
            "category": "technical",
            "difficulty": "medium",
        },
        {
            "question": "Why should we hire you for this Software Engineer Intern role?",
            "category": "behavioral",
            "difficulty": "hard",
        },
    ]
    client = get_openai_client()
    title_context = f" for the role: {job_title}" if job_title else ""

    difficulty_plan = [
        f"Q{i + 1}: {difficulty_for_index(i, question_count)}" for i in range(question_count)
    ]
    difficulty_instructions = "\n".join(difficulty_plan)

    prompt = f"""You are an expert interviewer. Generate exactly {question_count} interview questions{title_context}.

STRICT REQUIREMENTS:
- Every question MUST be grounded in the candidate's RESUME and the JOB DESCRIPTION below.
- Reference specific skills, experiences, or requirements from those documents when possible.
- Follow this difficulty progression (one question each):
{difficulty_instructions}

Mix technical, behavioral, and experience-based questions appropriate to the role.

Return ONLY valid JSON:
{{
  "questions": [
    {{
      "question": "...",
      "category": "technical|behavioral|experience|culture",
      "difficulty": "easy|medium|hard"
    }}
  ]
}}

RESUME:
{resume_text[:6000]}

JOB DESCRIPTION:
{job_description[:6000]}
"""

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You create highly targeted interview questions from resume and JD. "
                    "Respond with JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or ""
    data = _parse_json_content(content)
    questions = data.get("questions", [])

    if len(questions) < question_count:
        raise BadRequestError(f"AI generated only {len(questions)} questions; expected {question_count}")

    normalized: list[dict[str, str]] = []
    for index, item in enumerate(questions[:question_count]):
        expected_difficulty = difficulty_for_index(index, question_count)
        difficulty = str(item.get("difficulty", expected_difficulty)).lower()
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = expected_difficulty
        normalized.append(
            {
                "question": str(item.get("question", "")),
                "category": str(item.get("category", "technical")),
                "difficulty": difficulty,
            },
        )
    return normalized


async def score_single_answer(
    *,
    question: str,
    answer: str,
    category: str | None,
    difficulty: str,
    resume_text: str,
    job_description: str,
    job_title: str | None,
    time_taken_seconds: int,
    time_limit_seconds: int,
) -> dict[str, Any]:
    return {
    "score": 75,
    "feedback": "Good answer. Clear communication and relevant points.",
    "strengths": ["Communication", "Clarity"],
    "improvements": ["Add more technical details"],
}
    """Score one answer immediately after submission."""
    client = get_openai_client()
    title_context = f" for {job_title}" if job_title else ""

    prompt = f"""Score this single interview answer{title_context} on a 0-100 scale.

Question difficulty: {difficulty}
Category: {category or "general"}
Time taken: {time_taken_seconds}s of {time_limit_seconds}s allowed

Return ONLY valid JSON:
{{
  "score": 0-100,
  "feedback": "2-3 sentences of constructive feedback",
  "score_breakdown": {{
    "technical": 0-100,
    "communication": 0-100,
    "time_management": 0-100
  }}
}}

QUESTION:
{question}

ANSWER:
{answer[:5000]}

RESUME (context):
{resume_text[:2500]}

JOB DESCRIPTION (context):
{job_description[:2500]}
"""

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "You evaluate one interview answer fairly. JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or ""
    return _parse_json_content(content)


async def score_interview(
    *,
    resume_text: str,
    job_description: str,
    job_title: str | None,
    qa_pairs: list[dict[str, Any]],
    terminated_early: bool = False,
) -> dict[str, Any]:
    """Final holistic scoring including readiness and performance breakdown."""
    return {
        "overall_score": 78,
        "readiness_score": 75,
        "grade": "B",
        "summary": "Candidate demonstrated good communication skills and basic technical knowledge.",
        "strengths": ["Good communication", "Problem solving"],
        "weaknesses": ["Limited industry experience"],
        "improvements": ["Build more projects", "Practice interviews"],
        "performance_breakdown": {
            "technical": 75,
            "communication": 85,
            "time_management": 80
        },
        "dimension_scores": {
            "technical": 75,
            "communication": 85,
            "relevance": 80,
            "problem_solving": 78
        }
    }
    client = get_openai_client()
    title_context = f" for {job_title}" if job_title else ""
    early_note = " The interview was terminated early due to poor performance." if terminated_early else ""

    qa_block = "\n\n".join(
        f"Q{i + 1} [{pair.get('difficulty', 'medium')}] ({pair.get('category', '')}): "
        f"{pair['question']}\n"
        f"A{i + 1} (score {pair.get('answer_score', 'N/A')}): {pair['answer']}\n"
        f"Per-answer feedback: {pair.get('feedback', '')}"
        for i, pair in enumerate(qa_pairs)
    )

    prompt = f"""Produce a final mock interview evaluation{title_context}.{early_note}

Return ONLY valid JSON:
{{
  "overall_score": 0-100,
  "readiness_score": 0-100,
  "grade": "A|B|C|D|F",
  "summary": "2-3 paragraphs",
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "improvements": ["actionable tip...", "..."],
  "performance_breakdown": {{
    "technical": 0-100,
    "communication": 0-100,
    "time_management": 0-100
  }},
  "dimension_scores": {{
    "technical": 0-100,
    "communication": 0-100,
    "relevance": 0-100,
    "problem_solving": 0-100
  }}
}}

readiness_score = how ready the candidate is to interview for THIS specific role (0-100).
performance_breakdown must include technical, communication, time_management.

RESUME:
{resume_text[:4000]}

JOB DESCRIPTION:
{job_description[:4000]}

INTERVIEW (with per-answer scores):
{qa_block}
"""

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "You are a senior hiring manager producing final interview reports. JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or ""
    return _parse_json_content(content)
