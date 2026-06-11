import httpx
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from code_brief.config import Config
from code_brief.models import PRSummary, Risk
from code_brief.llm.prompt import SYSTEM_PROMPT, build_prompt
from code_brief.llm.chunker import needs_chunking, chunk_files


def clean_json(text: str) -> str:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]

    return cleaned.strip()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_api(config: Config, messages: list) -> str:
    with httpx.Client() as client:
        response = client.post(
            config.anthropic_endpoint,
            headers={
                "x-api-key": config.anthropic_api_key,
                "Content-Type": "application/json"
            },
            json={
                "model": config.model,
                "messages": messages,
                "max_tokens": 1024
            },
            timeout=60.0
        )
        response.raise_for_status()
        text = response.json()["content"][0]["text"]

        if not text:
            raise ValueError("Empty response from API")

        cleaned = clean_json(text)

        try:
            json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON response from API: {text[:200]}")

        return cleaned


def parse_response(response_text: str, config: Config, pr_title: str = "") -> PRSummary:
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        return PRSummary(
            pr_number=config.pr_number,
            repo=config.repo,
            title=pr_title,
            summary="CodeBrief was unable to parse the LLM response. Please review the diff manually.",
            risks=[],
            focus_areas=["Manual review required — LLM returned an invalid response."]
        )

    risks = [
        Risk(
            severity=r.get("severity", "LOW"),
            confidence=r.get("confidence", 0),
            description=r.get("description", "No description provided")
        )
        for r in data.get("risks", [])
        if r.get("description")
    ]

    return PRSummary(
        pr_number=config.pr_number,
        repo=config.repo,
        title=pr_title,
        summary=data.get("summary", "No summary available."),
        risks=risks,
        focus_areas=data.get("focus_areas", [])
    )


def call_claude(config: Config, files: list, pr_title: str = "") -> PRSummary:
    if not needs_chunking(files):
        prompt = build_prompt(files, pr_title=pr_title)
        messages = [
            {"role": "user", "content": f"{SYSTEM_PROMPT}\n\n{prompt}"}
        ]
        response_text = call_api(config, messages)
        return parse_response(response_text, config, pr_title=pr_title)

    else:
        chunks = chunk_files(files)
        all_risks = []
        all_focus_areas = []
        summaries = []

        for i, chunk in enumerate(chunks):
            chunk_diff = ""
            for f in chunk:
                chunk_diff += f"File: {f['filename']} (+{f['additions']} -{f['deletions']})\n"
                chunk_diff += f"{f['diff']}\n\n"

            prompt = f"""Please review the following pull request diff (chunk {i+1} of {len(chunks)}) and return the JSON review.

Important:
- Base conclusions only on the provided diff.
- Do not speculate about code that is not shown.
- Focus on correctness, reliability, security, performance, and operational impact.

{chunk_diff}"""

            messages = [
                {"role": "user", "content": f"{SYSTEM_PROMPT}\n\n{prompt}"}
            ]

            response_text = call_api(config, messages)

            try:
                data = json.loads(response_text)
            except json.JSONDecodeError:
                data = {"summary": "", "risks": [], "focus_areas": []}

            summaries.append(data.get("summary", ""))
            all_risks.extend([
                Risk(
                    severity=r.get("severity", "LOW"),
                    confidence=r.get("confidence", 0),
                    description=r.get("description", "No description provided")
                )
                for r in data.get("risks", [])
                if r.get("description")
            ])
            all_focus_areas.extend(data.get("focus_areas", []))

        return PRSummary(
            pr_number=config.pr_number,
            repo=config.repo,
            title=pr_title,
            summary=" ".join(summaries),
            risks=all_risks,
            focus_areas=all_focus_areas
        )