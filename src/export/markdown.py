from .base import Exporter


_TMPL = """---
title: "{title}"
exported_by: "agentwork"
---

{content}
"""


class MarkdownExporter(Exporter):
    def export(self, content: str, title: str, **kwargs) -> bytes:
        md = _TMPL.format(title=title.replace('"', '\\"'), content=content)
        return md.encode("utf-8")


