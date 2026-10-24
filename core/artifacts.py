import difflib
import os
from pathlib import Path

REPO_DIR = Path(os.getenv("DEMO_REPO_DIR", "demo_repo"))


def _resolve(file_path: str, repo_dir: Path):
    root = repo_dir.resolve()
    raw = Path(file_path)
    for candidate in (repo_dir / raw, raw, repo_dir / raw.name):
        try:
            resolved = candidate.resolve()
            resolved.relative_to(root)  # must stay inside the repo folder
        except (ValueError, OSError):
            continue
        if resolved.is_file():
            return resolved
    return None


def build_artifacts(patches, repo_dir=REPO_DIR) -> dict:
    repo_dir = Path(repo_dir)
    state = {}
    notes = []

    for p in patches or []:
        name = p.get("file_path", "")
        search = p.get("search_block", "") or ""
        replace = p.get("replace_block", "") or ""

        target = _resolve(name, repo_dir)
        if target is None:
            notes.append(f"{name}: file not found inside {repo_dir}")
            continue

        if target not in state:
            text = target.read_text(encoding="utf-8")
            state[target] = {"name": name, "before": text, "after": text}
        s = state[target]

        if search and search in s["after"]:
            s["after"] = s["after"].replace(search, replace, 1)
        elif replace and replace in s["before"]:
            s["before"] = s["before"].replace(replace, search, 1)
        else:
            notes.append(f"{name}: neither SEARCH nor REPLACE block found in the file")

    chunks, files = [], []
    for s in state.values():
        if s["before"] == s["after"]:
            continue
        diff = "".join(
            difflib.unified_diff(
                s["before"].splitlines(keepends=True),
                s["after"].splitlines(keepends=True),
                fromfile=f"a/{s['name']}",
                tofile=f"b/{s['name']}",
            )
        )
        if diff and not diff.endswith("\n"):
            diff += "\n"
        chunks.append(diff)
        files.append({"path": s["name"], "content": s["after"]})

    return {"patch": "".join(chunks), "files": files, "notes": notes}