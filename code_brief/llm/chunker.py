import tiktoken
from code_brief.config import Config
from code_brief.logger import get_logger

logger = get_logger("code_brief.chunker")


def count_tokens(text: str) -> int:
    encoder = tiktoken.get_encoding("cl100k_base")
    return len(encoder.encode(text))


def chunk_files(files: list, config: Config) -> list[list[dict]]:
    chunks = []
    current_chunk = []
    current_tokens = 0

    for f in files:
        file_tokens = count_tokens(f["diff"])
        logger.debug(f"{f['filename']} — {file_tokens} tokens")

        if current_tokens + file_tokens > config.max_tokens_per_chunk and current_chunk:
            chunks.append(current_chunk)
            current_chunk = [f]
            current_tokens = file_tokens
        else:
            current_chunk.append(f)
            current_tokens += file_tokens

    if current_chunk:
        chunks.append(current_chunk)

    logger.info(f"{len(files)} files grouped into {len(chunks)} chunks")
    return chunks


def needs_chunking(files: list, config: Config) -> bool:
    total = sum(count_tokens(f["diff"]) for f in files)
    logger.debug(f"Total diff tokens: {total} — limit: {config.max_tokens_per_chunk}")
    return total > config.max_tokens_per_chunk