from .base import Exporter


_INFO_TMPL = """[TTS Placeholder]
title: {title}
voice: {voice}
speed: {speed}
language: {lang}

Preview:
{preview}
"""


class TTSExporter(Exporter):
    def export(self, content: str, title: str, **kwargs) -> bytes:
        voice = kwargs.get("voice", "female")
        speed = float(kwargs.get("speed", 1.0))
        lang = kwargs.get("language", "zh-CN")
        preview = content[:200]
        return _INFO_TMPL.format(title=title, voice=voice, speed=speed, lang=lang, preview=preview).encode("utf-8")


