"""Validate the local skill catalog and package links without running skills."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PRIVATE = re.compile(
    r"[A-Za-z]:[/\\](?:Users|Agents)[/\\]|voice_experiments|private-clone"
    r"|reference_id\s*[:=]|sk-(?:proj-|live-)[A-Za-z0-9_-]+"
    r"|(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])",
    re.IGNORECASE,
)
LINK = re.compile(r"\]\(([^)\s]+)(?:\s+[^)]*)?\)")


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    try:
        catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
        assert catalog["schema_version"] == 1
        categories = catalog["categories"]
        skills = catalog["skills"]
        assert isinstance(categories, list) and isinstance(skills, list)
        assert categories and skills
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as exc:
        return [f"Invalid catalog: {type(exc).__name__}"]

    category_ids: set[str] = set()
    for category in categories:
        key = category.get("id", "") if isinstance(category, dict) else ""
        if not isinstance(key, str) or not SLUG.fullmatch(key):
            errors.append("Invalid category id")
        elif key in category_ids:
            errors.append(f"Duplicate category: {key}")
        else:
            category_ids.add(key)

    paths: set[str] = set()
    ids: set[str] = set()
    names: set[str] = set()
    try:
        readme = (root / "README.md").read_text(encoding="utf-8")
    except OSError:
        readme = ""
        errors.append("Root README is missing")

    for skill in skills:
        if not isinstance(skill, dict):
            errors.append("Skill entry must be an object")
            continue
        key, category, relative = (
            skill.get("id"),
            skill.get("category"),
            skill.get("path"),
        )
        if not isinstance(key, str) or not SLUG.fullmatch(key):
            errors.append("Invalid skill id")
            continue
        if key in ids:
            errors.append(f"Duplicate skill: {key}")
        ids.add(key)
        if category not in category_ids:
            errors.append(f"Unknown category: {key}")
        expected = f"skills/{category}/{key}"
        if relative != expected:
            errors.append(f"Noncanonical skill path: {key}")
            continue
        package = root / relative
        paths.add(relative)
        if not package.resolve().is_relative_to(root) or package.is_symlink():
            errors.append(f"Package escapes repository: {key}")
            continue
        if relative not in readme:
            errors.append(f"Skill missing from README index: {key}")
        for required in ("SKILL.md", "README.md"):
            if not (package / required).is_file():
                errors.append(f"Missing {required}: {key}")
        try:
            content = (package / "SKILL.md").read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        header = re.match(r"\A---\r?\n(.*?)\r?\n---", content, re.DOTALL)
        name = (
            re.search(r"^name:\s*([a-z0-9-]+)\s*$", header[1], re.M) if header else None
        )
        if not name or name[1] != skill.get("activation_name"):
            errors.append(f"Activation name mismatch: {key}")
        elif name[1] in names:
            errors.append(f"Duplicate activation name: {name[1]}")
        else:
            names.add(name[1])
        if skill.get("distribution") == "standalone":
            if not (package / "LICENSE").is_file():
                errors.append(f"Standalone package needs its license: {key}")
            for file in package.rglob("*"):
                if not file.is_file():
                    continue
                if file.is_symlink() or not file.resolve().is_relative_to(
                    package.resolve()
                ):
                    errors.append(f"Package file escapes its folder: {file.name}")
                    continue
                if file.suffix in {
                    ".md",
                    ".json",
                    ".yaml",
                    ".yml",
                    ".txt",
                    ".py",
                    ".js",
                }:
                    if PRIVATE.search(file.read_text(encoding="utf-8")):
                        errors.append(
                            f"Possible private asset or identifier: {file.relative_to(root)}"
                        )

    actual = {
        str(p.parent.relative_to(root)).replace("\\", "/")
        for p in (root / "skills").rglob("SKILL.md")
    }
    for path in sorted(actual - paths):
        errors.append(f"Uncatalogued skill: {path}")

    for markdown in root.rglob("*.md"):
        if ".git" in markdown.parts:
            continue
        content = markdown.read_text(encoding="utf-8")
        for match in LINK.finditer(content):
            target = match[1].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith("#"):
                continue
            destination = (markdown.parent / unquote(parsed.path)).resolve()
            if not destination.is_relative_to(root) or not destination.exists():
                errors.append(
                    f"Broken or external local link: {markdown.relative_to(root)} -> {target}"
                )
            package_root = next(
                (root / p for p in paths if markdown.is_relative_to(root / p)), None
            )
            if package_root and not destination.is_relative_to(package_root):
                errors.append(
                    f"Package link is not standalone: {markdown.relative_to(root)} -> {target}"
                )
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(
        "Catalog, package boundaries and Markdown links passed. No skill was executed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
