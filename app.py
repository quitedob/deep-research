"""Compatibility entry point; application implementation lives in backend.main."""
from backend.main import app, run

__all__ = ["app"]

if __name__ == "__main__":
    run()
