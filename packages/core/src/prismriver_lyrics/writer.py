import mutagen
from mutagen.flac import FLAC
from mutagen.id3 import USLT
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

from prismriver_lyrics.models import SyncedLyrics


class LyricsWriteError(Exception):
    """Raised when lyrics can't be written to an audio file."""


def write_lyrics(file_path: str, lyrics: str | SyncedLyrics) -> None:
    """Write `lyrics` into `file_path`'s tags, replacing any lyrics tag
    already there. Synced lyrics are stored as LRC-formatted text.

    Raises LyricsWriteError if the file can't be read, its format isn't
    one of the supported tag formats (ID3/MP3, FLAC, Ogg Vorbis/Opus,
    MP4/M4A), or it can't be saved.
    """
    text = _to_lrc(lyrics) if isinstance(lyrics, SyncedLyrics) else lyrics

    try:
        audio = mutagen.File(file_path)
    except Exception as exc:
        raise LyricsWriteError(f"failed to open {file_path}: {exc}") from exc

    if audio is None:
        raise LyricsWriteError(f"unrecognized audio format: {file_path}")

    if isinstance(audio, MP3):
        if audio.tags is None:
            audio.add_tags()
        audio.tags.setall(
            "USLT", [USLT(encoding=3, lang="eng", desc="", text=text)]
        )
    elif isinstance(audio, MP4):
        audio["\xa9lyr"] = text
    elif isinstance(audio, (FLAC, OggVorbis, OggOpus)):
        audio["LYRICS"] = text
    else:
        raise LyricsWriteError(
            f"unsupported audio format: {type(audio).__name__}"
        )

    try:
        audio.save()
    except Exception as exc:
        raise LyricsWriteError(f"failed to save {file_path}: {exc}") from exc


def _to_lrc(lyrics: SyncedLyrics) -> str:
    lines = []
    for line in lyrics.lines:
        minutes, rest_ms = divmod(line.time_ms, 60_000)
        seconds, centiseconds = divmod(rest_ms // 10, 100)
        lines.append(
            f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]{line.text}"
        )
    return "\n".join(lines)
