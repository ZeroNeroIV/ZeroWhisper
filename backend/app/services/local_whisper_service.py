"""
Local transcription via faster-whisper (CTranslate2, CPU, int8).
Model is downloaded on first use and cached to disk.
"""
import asyncio
import os
import tempfile
import logging

from app.config import settings

logger = logging.getLogger(__name__)

_model = None  # WhisperModel, loaded lazily


def _load_model():
    global _model
    if _model is not None:
        return _model

    from faster_whisper import WhisperModel  # noqa: PLC0415

    model_name = settings.local_whisper_model
    cache_dir = settings.whisper_cache_dir or None

    logger.info("Loading local Whisper model '%s' (first use may download ~500 MB)…", model_name)
    os.makedirs(cache_dir, exist_ok=True) if cache_dir else None

    _model = WhisperModel(
        model_name,
        device="cpu",
        compute_type="int8",
        download_root=cache_dir,
    )
    logger.info("Local Whisper model '%s' ready.", model_name)
    return _model


def _transcribe_sync(audio_path: str) -> str:
    model = _load_model()
    segments, info = model.transcribe(audio_path, beam_size=5, language=None)
    logger.debug("Detected language: %s (%.0f%%)", info.language, info.language_probability * 100)
    return " ".join(seg.text.strip() for seg in segments).strip()


async def transcribe(data: bytes, filename: str) -> str:
    suffix = ".ogg" if filename.endswith(".ogg") else ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
        tmp_path = f.name
    try:
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, _transcribe_sync, tmp_path)
        return text
    finally:
        os.unlink(tmp_path)
