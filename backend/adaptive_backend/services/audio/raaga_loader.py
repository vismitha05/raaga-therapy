from pathlib import Path


def list_raagas(base_path: str) -> list[str]:
    root = Path(base_path)
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])

