"""failpack export — share a golden pack as tar.gz / zip."""

from __future__ import annotations

import io
import json
import tarfile
import zipfile
from pathlib import Path

from failpack import __version__
from failpack.pack import read_meta, utc_now_iso
from failpack.paths import ASSERTIONS_NAME, META_NAME, require_pack

MANIFEST_NAME = "failpack-manifest.json"
FORMAT_VERSION = 1


def _default_output(pack_id: str) -> Path:
    return Path(f"{pack_id}.tgz")


def detect_archive_format(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".zip"):
        return "zip"
    if name.endswith((".tgz", ".tar.gz", ".tar")):
        return "tar"
    return "tar"


def _manifest(pack_id: str) -> dict:
    return {
        "format_version": FORMAT_VERSION,
        "pack_id": pack_id,
        "exported_at": utc_now_iso(),
        "failpack_version": __version__,
    }


def _iter_pack_files(pack: Path) -> list[Path]:
    files = [p for p in pack.rglob("*") if p.is_file()]
    files.sort(key=lambda p: p.relative_to(pack).as_posix())
    return files


def cmd_export(
    pack_id: str,
    *,
    output: Path | None = None,
    root: Path | None = None,
) -> Path:
    """Export a golden pack to a shareable archive.

    Archive layout::

        failpack-manifest.json
        <pack_id>/
          meta.json
          assertions.yaml
          expected/…
          artifacts/…
          transcript.jsonl
    """
    pack = require_pack(pack_id, root)
    assertions = pack / ASSERTIONS_NAME
    if not assertions.is_file():
        raise FileNotFoundError(
            f"Pack '{pack_id}' has no {ASSERTIONS_NAME}. "
            f"Promote it first: `failpack promote {pack_id}`."
        )
    meta = read_meta(pack)
    if meta.get("status") != "golden":
        raise ValueError(
            f"Pack '{pack_id}' is not golden (status={meta.get('status')!r}). "
            f"Run `failpack promote {pack_id}` before exporting."
        )
    if not (pack / META_NAME).is_file():
        raise FileNotFoundError(f"Pack '{pack_id}' is missing {META_NAME}")

    out = (output or _default_output(pack_id)).expanduser()
    if not out.is_absolute():
        out = Path.cwd() / out
    out.parent.mkdir(parents=True, exist_ok=True)
    fmt = detect_archive_format(out)

    manifest_blob = json.dumps(_manifest(pack_id), indent=2, sort_keys=True) + "\n"
    files = _iter_pack_files(pack)

    if fmt == "zip":
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(MANIFEST_NAME, manifest_blob)
            for path in files:
                arcname = f"{pack_id}/{path.relative_to(pack).as_posix()}"
                zf.write(path, arcname)
    else:
        mode = "w:gz" if out.name.lower().endswith((".tgz", ".tar.gz")) else "w"
        with tarfile.open(out, mode) as tf:
            manifest_info = tarfile.TarInfo(name=MANIFEST_NAME)
            manifest_bytes = manifest_blob.encode("utf-8")
            manifest_info.size = len(manifest_bytes)
            tf.addfile(manifest_info, io.BytesIO(manifest_bytes))
            for path in files:
                arcname = f"{pack_id}/{path.relative_to(pack).as_posix()}"
                tf.add(path, arcname=arcname, recursive=False)

    return out.resolve()
