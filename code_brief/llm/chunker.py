import tiktoken
from code_brief.config import Config
from code_brief.logger import get_logger

logger = get_logger("code_brief.chunker")

# file size categories (in tokens)
SMALL_FILE_LIMIT = 500
LARGE_FILE_LIMIT = 20000


def count_tokens(text: str) -> int:
    encoder = tiktoken.get_encoding("cl100k_base")
    return len(encoder.encode(text))


def categorise_file(diff: str, config: Config) -> str:
    tokens = count_tokens(diff)
    if tokens < SMALL_FILE_LIMIT:
        return "small"
    elif tokens <= config.max_tokens_per_chunk:
        return "medium"
    elif tokens <= LARGE_FILE_LIMIT:
        return "large"
    else:
        return "extremely_large"


def split_diff_into_lines(diff: str, config: Config) -> list[str]:
    """Split a large file diff into sub-chunks by line groups."""
    lines = diff.splitlines(keepends=True)
    sub_chunks = []
    current = ""
    current_tokens = 0

    for line in lines:
        line_tokens = count_tokens(line)
        if current_tokens + line_tokens > config.max_tokens_per_chunk and current:
            sub_chunks.append(current)
            current = line
            current_tokens = line_tokens
        else:
            current += line
            current_tokens += line_tokens

    if current:
        sub_chunks.append(current)

    return sub_chunks


def truncate_diff(diff: str, config: Config) -> tuple[str, bool]:
    """Truncate an extremely large file to the most changed hunks."""
    lines = diff.splitlines(keepends=True)
    truncated_lines = []
    current_tokens = 0
    was_truncated = False

    for line in lines:
        line_tokens = count_tokens(line)
        if current_tokens + line_tokens > config.max_tokens_per_chunk:
            was_truncated = True
            break
        truncated_lines.append(line)
        current_tokens += line_tokens

    return "".join(truncated_lines), was_truncated


def chunk_files(files: list, config: Config) -> list[dict]:
    chunks = []
    current_chunk_files = []
    current_tokens = 0
    truncated_files = []

    for f in files:
        tokens = count_tokens(f["diff"])
        category = categorise_file(f["diff"], config)
        logger.debug(f"{f['filename']} — {tokens} tokens — {category}")

        if category == "extremely_large":
            # flush current chunk first
            if current_chunk_files:
                chunks.append({
                    "files": current_chunk_files,
                    "truncated_files": [],
                    "type": "normal"
                })
                current_chunk_files = []
                current_tokens = 0

            # truncate and add as its own chunk with warning
            truncated_diff, was_truncated = truncate_diff(f["diff"], config)
            if was_truncated:
                truncated_files.append(f["filename"])
                logger.warning(f"{f['filename']} truncated — diff too large")

            truncated_file = {**f, "diff": truncated_diff}
            chunks.append({
                "files": [truncated_file],
                "truncated_files": [f["filename"]] if was_truncated else [],
                "type": "truncated"
            })

        elif category == "large":
            # flush current chunk first
            if current_chunk_files:
                chunks.append({
                    "files": current_chunk_files,
                    "truncated_files": [],
                    "type": "normal"
                })
                current_chunk_files = []
                current_tokens = 0

            # split into sub-chunks
            sub_chunks = split_diff_into_lines(f["diff"], config)
            logger.info(f"{f['filename']} split into {len(sub_chunks)} sub-chunks")
            chunks.append({
                "files": [f],
                "sub_chunks": sub_chunks,
                "truncated_files": [],
                "type": "large_file"
            })

        else:
            # small or medium — group into shared chunks
            if current_tokens + tokens > config.max_tokens_per_chunk and current_chunk_files:
                chunks.append({
                    "files": current_chunk_files,
                    "truncated_files": [],
                    "type": "normal"
                })
                current_chunk_files = [f]
                current_tokens = tokens
            else:
                current_chunk_files.append(f)
                current_tokens += tokens

    # flush remaining files
    if current_chunk_files:
        chunks.append({
            "files": current_chunk_files,
            "truncated_files": [],
            "type": "normal"
        })

    logger.info(f"{len(files)} files grouped into {len(chunks)} chunks")
    return chunks


def needs_chunking(files: list, config: Config) -> bool:
    total = sum(count_tokens(f["diff"]) for f in files)
    logger.debug(f"Total diff tokens: {total} — limit: {config.max_tokens_per_chunk}")
    return total > config.max_tokens_per_chunk


def needs_hierarchical_summarisation(files: list, config: Config) -> bool:
    """Check if the total diff is so large it needs multi-level summarisation."""
    total = sum(count_tokens(f["diff"]) for f in files)
    # if total tokens are more than 10x the chunk size, use hierarchical approach
    return total > config.max_tokens_per_chunk * 10