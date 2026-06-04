import httpx
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from code_brief.config import Config
from code_brief.models import PRSummary, Risk
from code_brief.llm.prompt import SYSTEM_PROMPT, build_prompt
from code_brief.llm.chunker import needs_chunking, chunk_files


def parse_response(response_text: str, config: Config, pr_title: str = "") -> PRSummary:
    data = json.loads(response_text)

    risks = [
        Risk(
            severity=r["severity"],
            confidence=r["confidence"],
            description=r["description"],
        )
        for r in data.get("risks", [])
    ]

    return PRSummary(
        pr_number=config.pr_number,
        repo=config.repo,
        title=pr_title,
        summary=data["summary"],
        risks=risks,
        focus_areas=data.get("focus_areas", [])
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_api(config: Config, messages: list) -> str:
    with httpx.Client() as client:
        response = client.post(
            config.anthropic_endpoint,
            headers={
                "x-api-key": config.anthropic_api_key,
                "Content-Type": "application/json",
            },
            json={
                "model": config.model,
                "messages": messages,
                "max_tokens": 1024
            },
            timeout=60.0
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]


def call_claude(config: Config, pr_title: str) -> PRSummary:
    if not needs_chunking(config):
        prompt = build_prompt(config, pr_title=pr_title)
        messages = [
            {"role": "user", "content": f"{SYSTEM_PROMPT}\n\n{prompt}"},
        ]
        response_text = call_api(config, messages)
        return parse_response(response_text, config, pr_title=pr_title)

    else:
        chunks = chunk_files(config)
        all_risks = []
        all_focus_areas = []
        summaries = []
        chunk_diff = ""

        for i, chunk in enumerate(chunks):
            chunk_diff = ""
            for f in chunk:
                chunk_diff += f"File: {f["filename"]} (+{f["additions"]} - {f["deletions"]})\n)"
                chunk_diff += f"{f["diff"]}\n\n"

        prompt = f"""Please review the following pull request diff (chunk {i + 1} of {len(chunks)}) and return the JSON review.

        Important:
        - Base conclusions only on the provided diff.
        - Do not speculate about code that is not shown.
        - Focus on correctness, reliability, security, performance, and operational impact.

        {chunk_diff}"""

        messages = [
            {"role": "user", "content": f"{SYSTEM_PROMPT}\n\n{prompt}"},
        ]
        response_text = call_api(config, messages)
        data = json.loads(response_text)
        summaries.append(data.get("summary", ""))
        all_risks.extend([
            Risk(
                severity=r["severity"],
                confidence=r["confidence"],
                description=r["description"]
            )
            for r in data.get("risks", [])
        ])
        all_focus_areas.extend([data.get("focus_areas", [])])

        return PRSummary(
            pr_number=config.pr_number,
            repo=config.repo,
            title=pr_title,
            summary=" ".join(summaries),
            risks=all_risks,
            focus_areas=all_focus_areas
        )
