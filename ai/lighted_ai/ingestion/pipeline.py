"""Fast ingestion pipeline for educational material.

This intentionally mirrors the important parts of the multimodal ingestion
system while dropping the graph database and orchestration-heavy layers that
are not needed in the isolated AI folder.
"""
from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

from lighted_ai.config import settings
from lighted_ai.embeddings import cosine_similarity, embed_batch

_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WHITESPACE_RE = re.compile(r"[ \t\f\v]+")

CHUNK_CHARACTERS = 1200
CHUNK_OVERLAP = 200
CHILD_CHUNK_CHARACTERS = 850
PARENT_CHUNK_CHARACTERS = 2400
MIN_PARENT_CHARACTERS = 350
SEMANTIC_BOUNDARY_THRESHOLD = 0.55
CHILD_SEMANTIC_BOUNDARY_THRESHOLD = 0.42
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_EXTRACTED_CHARACTERS = 2_000_000
MAX_CONTENT_UNITS = 10_000

PDF_MIME = "application/pdf"
PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
TXT_MIME = "text/plain"
AUDIO_MIME_PREFIX = "audio/"


class IngestionError(ValueError):
    """Raised when an uploaded material cannot be safely ingested."""


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    content: str
    chunk_level: str
    parent_chunk_id: str | None = None
    source_type: str = "text"
    location: str | None = None
    char_start: int | None = None
    char_end: int | None = None


@dataclass(slots=True)
class IngestedDocument:
    source_name: str
    source_type: str
    content: str
    chunks: list[Chunk] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class _TextUnit:
    text: str
    location: str


@dataclass(frozen=True, slots=True)
class _SourceRange:
    start: int
    end: int
    location: str


@dataclass(frozen=True, slots=True)
class _Sentence:
    text: str
    start: int
    end: int
    location: str | None


def _safe_filename(filename: str) -> str:
    if not isinstance(filename, str) or not filename.strip():
        raise IngestionError("filename must be a non-empty string")
    name = Path(filename.replace("\\", "/")).name.strip()
    if name in {"", ".", ".."} or "\x00" in name:
        raise IngestionError("Invalid filename")
    if len(name) > 255:
        raise IngestionError("Filename exceeds 255 characters")
    return name


def _validate_bytes(raw_bytes: bytes | bytearray | memoryview) -> bytes:
    if not isinstance(raw_bytes, (bytes, bytearray, memoryview)):
        raise IngestionError("file_bytes must be bytes-like")
    data = bytes(raw_bytes)
    if not data:
        raise IngestionError("Uploaded file is empty")
    if len(data) > MAX_FILE_BYTES:
        raise IngestionError(f"Uploaded file exceeds the {MAX_FILE_BYTES // (1024 * 1024)} MB limit")
    return data


def _tokenize(text: str) -> list[str]:
    return [token.casefold() for token in _TOKEN_RE.findall(text) if len(token) > 1]


def _normalise_text(text: str) -> str:
    if not isinstance(text, str):
        raise IngestionError("Extracted content must be text")
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.split("\n"):
        line = _WHITESPACE_RE.sub(" ", line).strip()
        if line:
            lines.append(line)
    return "\n\n".join(lines).strip()


def _stable_id(source_name: str, source_sha256: str, level: str, index: int) -> str:
    name_digest = hashlib.sha256(source_name.encode("utf-8")).hexdigest()[:10]
    return f"{name_digest}-{source_sha256[:12]}-{level}{index:05d}"


def _make_source_ranges(units: Sequence[_TextUnit]) -> tuple[str, list[_SourceRange]]:
    parts: list[str] = []
    ranges: list[_SourceRange] = []
    offset = 0
    for unit in units:
        text = _normalise_text(unit.text)
        if not text:
            continue
        if parts:
            parts.append("\n\n")
            offset += 2
        start = offset
        parts.append(text)
        offset += len(text)
        ranges.append(_SourceRange(start=start, end=offset, location=unit.location))
    return "".join(parts), ranges


def _location_at(offset: int, source_ranges: Sequence[_SourceRange], fallback: str | None) -> str | None:
    for item in source_ranges:
        if item.start <= offset < item.end:
            return item.location
    return fallback


def _split_long_sentence(text: str, start: int, location: str | None) -> list[_Sentence]:
    result: list[_Sentence] = []
    cursor = 0
    length = len(text)
    while cursor < length:
        hard_end = min(length, cursor + CHILD_CHUNK_CHARACTERS)
        end = hard_end
        if hard_end < length:
            boundary = text.rfind(" ", cursor + CHILD_CHUNK_CHARACTERS // 2, hard_end + 1)
            if boundary > cursor:
                end = boundary
        while cursor < end and text[cursor].isspace():
            cursor += 1
        raw_end = end
        while raw_end > cursor and text[raw_end - 1].isspace():
            raw_end -= 1
        if raw_end > cursor:
            result.append(_Sentence(text[cursor:raw_end], start + cursor, start + raw_end, location))
        cursor = max(end, cursor + 1)
        while cursor < length and text[cursor].isspace():
            cursor += 1
    return result


def _split_sentences(
    text: str,
    source_ranges: Sequence[_SourceRange] = (),
    fallback_location: str | None = None,
) -> list[_Sentence]:
    text = _normalise_text(text)
    if not text:
        return []
    sentences: list[_Sentence] = []
    for paragraph in re.split(r"\n+", text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        for match in re.finditer(r".+?(?:[.!?](?=\s|$)|$)", paragraph, re.DOTALL):
            raw = match.group(0).rstrip()
            if not raw:
                continue
            start = text.find(raw, 0 if not sentences else sentences[-1].end)
            if start < 0:
                start = 0
            end = start + len(raw)
            location = _location_at(start, source_ranges, fallback_location)
            if len(raw) > CHILD_CHUNK_CHARACTERS:
                sentences.extend(_split_long_sentence(raw, start, location))
            else:
                sentences.append(_Sentence(raw, start, end, location))
    if not sentences and text.strip():
        location = _location_at(0, source_ranges, fallback_location)
        sentences = _split_long_sentence(text.strip(), 0, location)
    return sentences


def semantic_parent_child_chunks(
    text: str,
    *,
    source_type: str = "text",
    source_name: str = "document",
    location: str | None = None,
    child_index_start: int = 0,
    parent_index_start: int = 0,
    source_ranges: Sequence[_SourceRange] = (),
    source_sha256: str | None = None,
) -> list[Chunk]:
    """Build parent chunks with embedded child chunks for retrieval.

    This keeps the original semantic chunking strategy while adding stable IDs,
    source-location tracking, and validation hygiene from the broader ingestion pipeline.
    """
    normalized = _normalise_text(text)
    sentences = _split_sentences(normalized, source_ranges, location)
    if not sentences:
        return []
    try:
        vectors = embed_batch([sentence.text for sentence in sentences], task_type="RETRIEVAL_DOCUMENT")
    except Exception as exc:  # pragma: no cover - network/provider dependent
        raise IngestionError("Unable to embed study text for semantic chunking") from exc

    if len(vectors) != len(sentences):
        raise IngestionError("Embedding count does not match sentence count")

    parent_groups: list[list[int]] = []
    current: list[int] = []
    current_chars = 0
    for idx, sentence in enumerate(sentences):
        sentence_len = len(sentence.text)
        semantic_break = (
            bool(current)
            and current_chars >= MIN_PARENT_CHARACTERS
            and cosine_similarity(vectors[current[-1]], vectors[idx]) < SEMANTIC_BOUNDARY_THRESHOLD
        )
        size_break = bool(current) and current_chars + sentence_len + 1 > PARENT_CHUNK_CHARACTERS
        if semantic_break or size_break:
            parent_groups.append(current)
            current = []
            current_chars = 0
        current.append(idx)
        current_chars += sentence_len + 1
    if current:
        parent_groups.append(current)

    chunks: list[Chunk] = []
    next_child_index = child_index_start
    next_parent_index = parent_index_start
    digest = source_sha256 or hashlib.sha256((source_name + "\0" + normalized).encode("utf-8")).hexdigest()

    def make_chunk_location(indices: Sequence[int]) -> str | None:
        locations: list[str] = []
        for idx in indices:
            value = sentences[idx].location or location
            if value and value not in locations:
                locations.append(value)
        return ", ".join(locations) if locations else location

    for parent_sentences in parent_groups:
        first = parent_sentences[0]
        last = parent_sentences[-1]
        parent_id = _stable_id(source_name, digest, "p", next_parent_index)
        parent_text = normalized[sentences[first].start:sentences[last].end].strip()
        chunks.append(
            Chunk(
                chunk_id=parent_id,
                content=parent_text,
                chunk_level="parent",
                source_type=source_type,
                location=make_chunk_location(parent_sentences),
                char_start=sentences[first].start,
                char_end=sentences[last].end,
            )
        )
        next_parent_index += 1

        child_groups: list[list[int]] = []
        child_group: list[int] = []
        child_chars = 0
        for sentence_index in parent_sentences:
            sentence_len = len(sentences[sentence_index].text)
            semantic_break = (
                bool(child_group)
                and child_chars >= CHILD_CHUNK_CHARACTERS // 2
                and cosine_similarity(vectors[child_group[-1]], vectors[sentence_index])
                < CHILD_SEMANTIC_BOUNDARY_THRESHOLD
            )
            size_break = bool(child_group) and child_chars + sentence_len + 1 > CHILD_CHUNK_CHARACTERS
            if semantic_break or size_break:
                child_groups.append(child_group)
                child_group = []
                child_chars = 0
            child_group.append(sentence_index)
            child_chars += sentence_len + 1

        if child_group:
            child_groups.append(child_group)

        for child_group in child_groups:
            child_first = child_group[0]
            child_last = child_group[-1]
            child_id = _stable_id(source_name, digest, "c", next_child_index)
            child_text = normalized[sentences[child_first].start:sentences[child_last].end].strip()
            chunks.append(
                Chunk(
                    chunk_id=child_id,
                    content=child_text,
                    chunk_level="child",
                    parent_chunk_id=parent_id,
                    source_type=source_type,
                    location=make_chunk_location(child_group),
                    char_start=sentences[child_first].start,
                    char_end=sentences[child_last].end,
                )
            )
            next_child_index += 1

    return chunks


def _read_text_bytes(raw_bytes: bytes, *, filename: str) -> str:
    if not raw_bytes:
        raise IngestionError("Uploaded file is empty")
    if len(raw_bytes) > MAX_FILE_BYTES:
        raise IngestionError("Uploaded file exceeds the 25 MB limit")

    lower_name = filename.lower()
    if lower_name.endswith(".txt"):
        try:
            return raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return raw_bytes.decode("latin-1")
            except UnicodeDecodeError as exc:
                raise IngestionError("Text file is not valid UTF-8/Latin-1 text") from exc

    if lower_name.endswith(".pdf"):
        try:
            import pypdf
        except ImportError as exc:  # pragma: no cover
            raise IngestionError("pypdf is required for PDF ingestion") from exc
        reader = pypdf.PdfReader(__import__("io").BytesIO(raw_bytes))
        pages: list[str] = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n\n".join(pages)

    if lower_name.endswith(".pptx"):
        try:
            from pptx import Presentation
        except ImportError as exc:  # pragma: no cover
            raise IngestionError("python-pptx is required for PPTX ingestion") from exc
        presentation = Presentation(__import__("io").BytesIO(raw_bytes))
        slides: list[str] = []
        for slide in presentation.slides:
            bits: list[str] = []
            for shape in slide.shapes:
                if getattr(shape, "has_text_frame", False):
                    bits.append(shape.text)
            slides.append("\n".join(b for b in bits if b))
        return "\n\n".join(slides)

    raise IngestionError("Unsupported file type. Supported: .txt, .pdf, .pptx")


def _read_audio_text(raw_bytes: bytes, *, filename: str) -> str:
    lower_name = filename.lower()
    if not lower_name.endswith((".mp3", ".wav", ".m4a", ".ogg", ".flac")):
        raise IngestionError("Unsupported audio type. Supported: .mp3, .wav, .m4a, .ogg, .flac")
    try:
        from pydub import AudioSegment
    except ImportError as exc:  # pragma: no cover
        raise IngestionError("pydub is required for audio ingestion") from exc

    try:
        audio = AudioSegment.from_file(__import__("io").BytesIO(raw_bytes))
        # make audio transcription-friendly and avoid large processing spikes
        audio = audio.set_channels(1)
        segments = list(audio[::10000])
        texts: list[str] = []
        for idx, segment in enumerate(segments):
            texts.append(f"[audio segment {idx + 1}] {segment.duration_seconds:.1f}s")
        return "\n".join(texts)
    except Exception as exc:
        raise IngestionError("Audio file could not be processed") from exc


def ingest_file(
    file_bytes: bytes | bytearray | memoryview,
    filename: str,
) -> IngestedDocument:
    """Ingest a single supported file into stable parent/child chunks."""
    raw_bytes = _validate_bytes(file_bytes)
    name = _safe_filename(filename)
    lower_name = name.lower()

    if lower_name.endswith((".txt", ".pdf", ".pptx")):
        content = _read_text_bytes(raw_bytes, filename=name)
        source_type = "document"
    elif lower_name.endswith((".mp3", ".wav", ".m4a", ".ogg", ".flac")):
        content = _read_audio_text(raw_bytes, filename=name)
        source_type = "audio"
    else:
        raise IngestionError("Unsupported input type")

    normalized = _normalise_text(content)
    if not normalized:
        raise IngestionError("No readable text found in the uploaded file")
    if len(normalized) > MAX_EXTRACTED_CHARACTERS:
        raise IngestionError("Extracted text exceeds the 2 MB processing limit")

    source_hash = hashlib.sha256(raw_bytes).hexdigest()
    chunks = semantic_parent_child_chunks(
        normalized,
        source_type=source_type,
        source_name=name,
        location=name,
        source_sha256=source_hash,
    )
    if not chunks:
        raise IngestionError("No chunks could be created from the uploaded file")
    if len(chunks) > MAX_CONTENT_UNITS:
        raise IngestionError("The uploaded file creates too many parent and child chunks")

    metadata = {
        "filename": name,
        "mime_type": _detect_mime(name),
        "size_bytes": len(raw_bytes),
        "sha256": source_hash,
        "extracted_characters": len(normalized),
        "chunk_count": len(chunks),
        "parent_chunk_count": sum(chunk.chunk_level == "parent" for chunk in chunks),
        "child_chunk_count": sum(chunk.chunk_level == "child" for chunk in chunks),
    }
    return IngestedDocument(
        source_name=name,
        source_type=source_type,
        content=normalized,
        chunks=chunks,
        metadata=metadata,
    )


def ingest_files(
    files: Sequence[tuple[bytes | bytearray | memoryview, str]] | Iterable[tuple[bytes | bytearray | memoryview, str]],
) -> list[IngestedDocument]:
    """Batch ingest multiple files while preserving the current module scope."""
    return [ingest_file(file_bytes, filename) for file_bytes, filename in list(files)]


def _detect_mime(filename: str) -> str:
    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        return PDF_MIME
    if lower_name.endswith(".pptx"):
        return PPTX_MIME
    if lower_name.endswith(".txt"):
        return TXT_MIME
    if lower_name.endswith((".mp3", ".wav", ".m4a", ".ogg", ".flac")):
        return "audio/mpeg" if lower_name.endswith(".mp3") else f"{AUDIO_MIME_PREFIX}{lower_name.rsplit('.', 1)[-1]}"
    return "application/octet-stream"
