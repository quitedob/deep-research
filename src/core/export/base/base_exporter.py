from abc import ABC, abstractmethod
from pathlib import Path


class Exporter(ABC):
    """导出器抽象基类：统一 export()->bytes 与 save_to_file() 行为。"""

    @abstractmethod
    def export(self, content: str, title: str, **kwargs) -> bytes:
        ...

    def save_to_file(self, content: str, title: str, output_path: Path, **kwargs) -> Path:
        data = self.export(content=content, title=title, **kwargs)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(data)
        return output_path


