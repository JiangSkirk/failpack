# Publishing FailPack to PyPI / TestPyPI

**Status:** FailPack is live on PyPI since **1.5.5**
([pypi.org/project/failpack](https://pypi.org/project/failpack/)). Strangers
should install with:

```bash
pip install failpack
failpack demo --fast
failpack demo --claude-hermetic
failpack demo --cursor-hermetic
```

Git fallback (optional):

```bash
pip install "git+https://github.com/JiangSkirk/failpack.git"
```

This doc is the exact path to publish a **new** release to **TestPyPI** or
**PyPI** when you have a token. **Do not upload without a token in the
environment.** Do not re-upload an already-published version.

## Prerequisites

- Python **3.11+**
- A clean checkout on the release tag (e.g. `v1.5.11`)
- Build tools:

```bash
python -m pip install -U build twine
```

## 1. Verify metadata + version

```bash
grep -E '^version|^__version__' pyproject.toml src/failpack/__init__.py
# both should match the release (e.g. 1.5.11)

failpack --version   # after editable install
```

Confirm `README.md` is the long description (set via `readme = "README.md"` in
`pyproject.toml`), and that classifiers / project URLs look right.

## 2. Build sdist + wheel

```bash
rm -rf dist/ build/
python -m build
ls -la dist/
# expect: failpack-<ver>.tar.gz  and  failpack-<ver>-py3-none-any.whl
```

## 3. Check the artifacts (no upload)

```bash
python -m twine check dist/*
# expect: PASSED for both files
```

Optional smoke install from the local wheel:

```bash
python -m pip install --force-reinstall "dist/failpack-"*-py3-none-any.whl
failpack --version
failpack demo --skip-break --no-keep
```

## 4. TestPyPI (recommended first)

Create an API token at https://test.pypi.org/manage/account/token/  
Export it (never commit):

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-...   # TestPyPI token
```

Upload:

```bash
python -m twine upload --repository testpypi dist/*
```

Install from TestPyPI (PyYAML still comes from real PyPI):

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  failpack
failpack --version
failpack demo --skip-break --no-keep
```

## 5. PyPI (production)

Create an API token at https://pypi.org/manage/account/token/  

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-...   # PyPI token
python -m twine upload dist/*
```

Then strangers can:

```bash
pip install failpack
failpack demo --fast
```

## 6. After publish

- Create / confirm the GitHub Release tag matching the version
- Update Action pins / docs if this release is the new recommended `@vX.Y.Z`
  (quality-freeze docs cuts usually keep `@v1.5.0` when Action behavior is
  unchanged)
- Prefer Trusted Publishing (OIDC) from GitHub Actions when available instead of
  long-lived tokens
- Confirm [pypi.org/project/failpack](https://pypi.org/project/failpack/) shows
  the new version; in-tree Quickstart stays `pip install failpack` first

## Non-goals

- Do **not** upload if `TWINE_PASSWORD` / token is missing
- Do **not** re-upload a version that is already on PyPI
- No monetization / checkout wiring in this publish path
- No coupling to Echo / Orin / titan-agent
