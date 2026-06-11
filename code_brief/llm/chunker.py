import tiktoken

MAX_TOKENS = 6000


def count_tokens(text: str) -> int:
    encoder = tiktoken.get_encoding("cl100k_base")
    return len(encoder.encode(text))


def chunk_files(files: list) -> list[list[dict]]:
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


def needs_chunking(files: list) -> bool:
    total = sum(count_tokens(f["diff"]) for f in files)
    return total > MAX_TOKENS