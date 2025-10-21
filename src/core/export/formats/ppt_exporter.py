from .base import Exporter


_SLIDES_TMPL = """---
marp: true
paginate: true
theme: default
title: "{title}"
---

# {title}

{content}
"""


class PPTExporter(Exporter):
    def export(self, content: str, title: str, **kwargs) -> bytes:
        return _SLIDES_TMPL.format(title=title.replace('"', '\\"'), content=content).encode("utf-8")


