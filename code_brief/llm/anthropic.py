import httpx
import json
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from code_brief.config import Config
from code_brief.models import PRSummary, Risk
from code_brief.llm.prompt import SYSTEM_PROMPT, build_prompt
from code_brief.llm.chunker import needs_chunking, chunk_files
from code_brief.logger import get_logger

logger = get_logger("code_brief.llm")


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


def make_api_caller(config: Config):
    @retry(
        stop=stop_after_attempt(config.max_retries),
        wait=wait_exponential(multiplier=1, min=config.retry_wait_min, max=config.retry_wait_max)
    )
    def call_api(messages: list) -> str:
        start = time.time()
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
                    "max_tokens": config.llm_max_tokens
                },
                timeout=config.api_timeout
            )
            response.raise_for_status()
            text = response.json()["content"][0]["text"]

            if not text:
                logger.warning("Empty response from API — retrying")
                raise ValueError("Empty response from API")

            cleaned = clean_json(text)

            try:
                json.loads(cleaned)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON response — retrying. Preview: {text[:100]}")
                raise ValueError(f"Invalid JSON response from API: {text[:200]}")

            elapsed = round(time.time() - start, 2)
            logger.info(f"API response received in {elapsed}s")
            return cleaned

    return call_api


def parse_response(response_text: str, config: Config, pr_title: str = "") -> PRSummary:
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM response after all retries — returning fallback summary")
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

    logger.info(f"Parsed response — {len(risks)} risks, {len(data.get('focus_areas', []))} focus areas")
    return PRSummary(
        pr_number=config.pr_number,
        repo=config.repo,
        title=pr_title,
        summary=data.get("summary", "No summary available."),
        risks=risks,
        focus_areas=data.get("focus_areas", [])
    )


def call_claude(config: Config, files: list, pr_title: str = "") -> PRSummary:
    call_api = make_api_caller(config)
    start = time.time()

    if not needs_chunking(files, config):
        logger.info("Diff within token limit — sending in single pass")
        prompt = build_prompt(files, pr_title=pr_title)
        messages = [
            {"role": "user", "content": f"{SYSTEM_PROMPT}\n\n{prompt}"}
        ]
        response_text = call_api(messages)
        summary = parse_response(response_text, config, pr_title=pr_title)
    else:
        chunks = chunk_files(files, config)
        logger.info(f"Large diff — processing {len(chunks)} chunks")
        all_risks = []
        all_focus_areas = []
        summaries = []

        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
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

            response_text = call_api(messages)

            try:
                data = json.loads(response_text)
            except json.JSONDecodeError:
                logger.warning(f"Chunk {i+1} parse failed — skipping")
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

        summary = PRSummary(
            pr_number=config.pr_number,
            repo=config.repo,
            title=pr_title,
            summary=" ".join(summaries),
            risks=all_risks,
            focus_areas=all_focus_areas
        )

    elapsed = round(time.time() - start, 2)
    logger.info(f"Total processing time: {elapsed}s")
    return summary