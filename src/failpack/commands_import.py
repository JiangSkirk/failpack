"""failpack import — restore a shared pack archive into .failpack/packs/."""

from __future__ import annotations

import json
import re
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path

from failpack.commands_export import MANIFEST_NAME, detect_archive_format
from failpack.commands_init import cmd_init
from failpack.pack import read_meta, write_meta
from failpack.paths import META_NAME, find_root, pack_dir, packs_dir

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _validate_pack_id(pack_id: str) -> str:
    if not _SAFE_ID.match(pack_id):
        raise ValueError(
            f"Invalid pack id {pack_id!r}. Use letters, digits, '.', '_', '-' "
            "(max 128 chars)."
        )
    return pack_id


def _within(directory: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def _extract_archive(archive: Path, dest: Path) -> None:
    fmt = detect_archive_format(archive)
    if fmt == "zip":
        with zipfile.ZipFile(archive) as zf:
            for info in zf.infolist():
                name = info.filename
                if name.startswith("/") or ".." in Path(name).parts:
                    raise ValueError(f"Refusing unsafe archive member: {name!r}")
                target = (dest / name).resolve()
                if not _within(dest, target) and target != dest.resolve():
                    raise ValueError(f"Refusing archive member outside dest: {name!r}")
            zf.extractall(dest)
    else:
        with tarfile.open(archive, "r:*") as tf:
            for member in tf.getmembers():
                name = member.name
                if name.startswith("/") or ".." in Path(name).parts:
                    raise ValueError(f"Refusing unsafe archive member: {name!r}")
                target = (dest / name).resolve()
                if not _within(dest, target) and target != dest.resolve():
                    raise ValueError(f"Refusing archive member outside dest: {name!r}")
            # filter= added in 3.12; keep 3.11-safe fallback.
            try:
                tf.extractall(dest, filter="data")
            except TypeError:
                tf.extractall(dest)


def _load_manifest(extracted: Path) -> dict | None:
    path = extracted / MANIFEST_NAME
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid {MANIFEST_NAME}")
    return data


def _find_pack_root(extracted: Path, preferred_id: str | None) -> Path:
    """Locate the pack directory containing meta.json inside an extracted archive."""
    if preferred_id:
        candidate = extracted / preferred_id
        if (candidate / META_NAME).is_file():
            return candidate

    metas = sorted(p for p in extracted.rglob(META_NAME) if p.is_file())
    if not metas:
        raise FileNotFoundError(
            f"No {META_NAME} found in archive. Export a FailPack pack first "
            "(`failpack export <id>`)."
        )
    packs = [m.parent for m in metas]
    packs.sort(key=lambda p: len(p.relative_to(extracted).parts))
    return packs[0]


def _unique_id(base: str, root: Path) -> str:
    """Pick ``base-imported``, ``base-imported-2``, … when *base* collides."""
    packs = packs_dir(root)
    candidate = f"{base}-imported"
    if not (packs / candidate).exists():
        return candidate
    n = 2
    while (packs / f"{candidate}-{n}").exists():
        n += 1
    return f"{candidate}-{n}"


def cmd_import(
    archive: Path,
    *,
    root: Path | None = None,
    force: bool = False,
    rename: str | None = None,
    auto_rename: bool = False,
) -> Path:
    """Import a pack archive into ``.failpack/packs/``.

    Collision handling:
    - ``force`` — overwrite the existing pack id
    - ``rename`` — import under a new id (updates ``meta.json``)
    - ``auto_rename`` — pick ``<id>-imported`` (or ``-2``, …) on collision
    - otherwise raise ``FileExistsError``
    """
    archive = archive.expanduser().resolve()
    if not archive.is_file():
        raise FileNotFoundError(f"Archive not found: {archive}")

    project = find_root(root) if root is None else root.resolve()
    if not packs_dir(project).is_dir():
        cmd_init(project)

    with tempfile.TemporaryDirectory(prefix="failpack-import-") as tmp:
        extracted = Path(tmp) / "extracted"
        extracted.mkdir()
        _extract_archive(archive, extracted)

        manifest = _load_manifest(extracted)
        preferred = None
        if manifest and isinstance(manifest.get("pack_id"), str):
            preferred = manifest["pack_id"]

        src_pack = _find_pack_root(extracted, preferred)
        source_id = src_pack.name
        meta = read_meta(src_pack)
        if isinstance(meta.get("id"), str) and meta["id"]:
            source_id = meta["id"]

        target_id = rename if rename is not None else source_id
        target_id = _validate_pack_id(target_id)

        dest = pack_dir(target_id, project)
        if dest.exists():
            if force:
                shutil.rmtree(dest)
            elif auto_rename and rename is None:
                target_id = _validate_pack_id(_unique_id(source_id, project))
                dest = pack_dir(target_id, project)
            else:
                suggestion = _unique_id(source_id, project)
                raise FileExistsError(
                    f"Pack '{target_id}' already exists under {packs_dir(project)}. "
                    f"Pass --force to overwrite, --rename {suggestion}, "
                    "or another --rename id."
                )

        shutil.copytree(src_pack, dest)

        meta = read_meta(dest)
        if meta.get("id") != target_id:
            meta["id"] = target_id
            write_meta(dest, meta)

        return dest
