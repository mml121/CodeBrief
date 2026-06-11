import httpx
import json
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from code_brief.config import Config
from code_brief.models import PRSummary, Risk
from code_brief.llm.prompt import SYSTEM_PROMPT, build_prompt
from code_brief.llm.chunker import needs_chunking, needs_hierarchical_summarisation, chunk_files
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


def make_api_caller(config: Config, metrics=None):
    @retry(
        stop=stop_after_attempt(config.max_retries),
        wait=wait_exponential(multiplier=1, min=config.retry_wait_min, max=config.retry_wait_max)
    )
    def call_api(messages: list) -> str:
        start = time.time()
        if metrics:
            metrics.llm_request_count += 1
        try:
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
                response_json = response.json()
                text = response_json["content"][0]["text"]

                # track token usage from API response
                input_tokens = response_json.get("usage", {}).get("input_tokens", 0)
                output_tokens = response_json.get("usage", {}).get("output_tokens", 0)
                if metrics:
                    metrics.input_tokens += input_tokens
                    metrics.output_tokens += output_tokens
                    metrics.total_tokens += input_tokens + output_tokens

                if not text:
                    if metrics:
                        metrics.retry_count += 1
                    logger.warning("Empty response from API - retrying")
                    raise ValueError("Empty response from API")

                cleaned = clean_json(text)

                try:
                    json.loads(cleaned)
                except json.JSONDecodeError:
                    if metrics:
                        metrics.retry_count += 1
                    logger.warning(f"Invalid JSON response - retrying. Preview: {text[:100]}")
                    raise ValueError(f"Invalid JSON response from API: {text[:200]}")

                elapsed = round(time.time() - start, 2)
                if metrics:
                    metrics.response_times.append(elapsed)
                logger.info(f"API response received in {elapsed}s")
                return cleaned

        except Exception as e:
            if metrics:
                metrics.failed_requests += 1
            raise e

    return call_api


def parse_response(response_text: str, config: Config, pr_title: str = "") -> PRSummary:
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM response - returning fallback summary")
        return PRSummary(
            pr_number=config.pr_number,
            repo=config.repo,
            title=pr_title,
            summary="CodeBrief was unable to parse the LLM response. Please review the diff manually.",
            risks=[],
            focus_areas=["Manual review required - LLM returned an invalid response."]
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

    logger.info(f"Parsed response - {len(risks)} risks, {len(data.get('focus_areas', []))} focus areas")
    return PRSummary(
        pr_number=config.pr_number,
        repo=config.repo,
        title=pr_title,
        summary=data.get("summary", "No summary available."),
        risks=risks,
        focus_areas=data.get("focus_areas", [])
    )


def process_chunk(chunk: dict, config: Config, call_api, chunk_index: int, total_chunks: int) -> dict:
    chunk_type = chunk.get("type", "normal")

    if chunk_type == "large_file":
        sub_chunks = chunk.get("sub_chunks", [])
        file = chunk["files"][0]
        summaries = []
        all_risks = []
        all_focus_areas = []

        for j, sub_diff in enumerate(sub_chunks):
            logger.info(f"Processing sub-chunk {j+1}/{len(sub_chunks)} of {file['filename']}")
            prompt = f"""Please review the following partial diff for file {file['filename']} (part {j+1} of {len(sub_chunks)}) and return the JSON review.

Important:
- This is only part of the file - do not assume anything about code not shown.
- Focus on correctness, reliability, security, performance, and operational impact.

File: {file['filename']} (+{file['additions']} -{file['deletions']})
{sub_diff}"""

            messages = [{"role": "user", "content": f"{SYSTEM_PROMPT}\n\n{prompt}"}]
            response_text = call_api(messages)
            try:
                data = json.loads(response_text)
                summaries.append(data.get("summary", ""))
                all_risks.extend(data.get("risks", []))
                all_focus_areas.extend(data.get("focus_areas", []))
            except json.JSONDecodeError:
                logger.warning(f"Sub-chunk {j+1} parse failed - skipping")

        return {
            "summary": " ".join(summaries),
            "risks": all_risks,
            "focus_areas": all_focus_areas
        }

    else:
        files = chunk["files"]
        truncated = chunk.get("truncated_files", [])

        chunk_diff = ""
        for f in files:
            chunk_diff += f"File: {f['filename']} (+{f['additions']} -{f['deletions']})\n"
            if f["filename"] in truncated:
                chunk_diff += "[NOTE: This file was truncated due to size - partial diff shown]\n"
            chunk_diff += f"{f['diff']}\n\n"

        prompt = f"""Please review the following pull request diff (chunk {chunk_index+1} of {total_chunks}) and return the JSON review.

Important:
- Base conclusions only on the provided diff.
- Do not speculate about code that is not shown.
- Focus on correctness, reliability, security, performance, and operational impact.

{chunk_diff}"""

        messages = [{"role": "user", "content": f"{SYSTEM_PROMPT}\n\n{prompt}"}]
        response_text = call_api(messages)

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning(f"Chunk {chunk_index+1} parse failed - skipping")
            return {"summary": "", "risks": [], "focus_areas": []}


def hierarchical_summarise(chunk_summaries: list[str], config: Config, call_api, pr_title: str) -> str:
    combined = "\n\n".join([f"Chunk {i+1} summary:\n{s}" for i, s in enumerate(chunk_summaries) if s])

    prompt = f"""You are given summaries from multiple chunks of a large pull request titled "{pr_title}".
Synthesise them into a single coherent 2-3 sentence PR summary.
Return ONLY a JSON object with this structure:
{{"summary": "..."}}

Chunk summaries:
{combined}"""

    messages = [{"role": "user", "content": prompt}]
    try:
        response_text = call_api(messages)
        data = json.loads(response_text)
        return data.get("summary", " ".join(chunk_summaries))
    except Exception:
        return " ".join(s for s in chunk_summaries if s)


def call_claude(config: Config, files: list, pr_title: str = "", metrics=None) -> PRSummary:
    from code_brief.metrics import Metrics as MetricsClass
    if metrics is None:
        metrics = MetricsClass()

    call_api = make_api_caller(config, metrics)
    start = time.time()

    if not needs_chunking(files, config):
        logger.info("Diff within token limit - sending in single pass")
        metrics.chunk_count = 1
        prompt = build_prompt(files, pr_title=pr_title)
        messages = [{"role": "user", "content": f"{SYSTEM_PROMPT}\n\n{prompt}"}]
        response_text = call_api(messages)
        summary = parse_response(response_text, config, pr_title=pr_title)

    else:
        chunks = chunk_files(files, config)
        metrics.chunk_count = len(chunks)

        use_hierarchical = needs_hierarchical_summarisation(files, config)
        if use_hierarchical:
            logger.info(f"Very large PR - using hierarchical summarisation across {len(chunks)} chunks")
        else:
            logger.info(f"Large diff - processing {len(chunks)} chunks")

        all_risks = []
        all_focus_areas = []
        chunk_summaries = []

        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            data = process_chunk(chunk, config, call_api, i, len(chunks))
            chunk_summaries.append(data.get("summary", ""))
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

        if use_hierarchical and len(chunk_summaries) > 3:
            logger.info("Running hierarchical summarisation pass")
            final_summary = hierarchical_summarise(chunk_summaries, config, call_api, pr_title)
        else:
            final_summary = " ".join(s for s in chunk_summaries if s)

        summary = PRSummary(
            pr_number=config.pr_number,
            repo=config.repo,
            title=pr_title,
            summary=final_summary,
            risks=all_risks,
            focus_areas=all_focus_areas
        )

    elapsed = round(time.time() - start, 2)
    logger.info(f"Total processing time: {elapsed}s")
    return summary