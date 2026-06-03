import tiktoken
from code_brief.github.diff import get_changed_files
from code_brief.config import Config

MAX_TOKENS = 6000


def count_tokens(text: str) -> int:
    encoder = tiktoken.get_encoding("cl100k_base")
    return len(encoder.encode(text))


def chunk_files(config: Config) -> list[list[dict]]:
    files = get_changed_files(config)
    chunks = []
    current_chunk = []
    current_tokens = 0

    for f in files:
        file_tokens = count_tokens(f["diff"])

        if current_tokens + file_tokens > MAX_TOKENS and current_chunk:
            chunks.append(current_chunk)
            current_chunk = [f]
            current_tokens = file_tokens
        else:
            current_chunk.append(f)
            current_tokens += file_tokens

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def needs_chunking(config: Config) -> bool:
    files = get_changed_files(config)
    total = sum([count_tokens(f["diff"]) for f in files])
    return total > MAX_TOKENS
