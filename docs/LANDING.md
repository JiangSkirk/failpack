# FailPack — English landing copy
# Paste into a static page (Framer / Carrd / Cloudflare Pages / plain HTML).
# Product is regression memory for coding-agent failures — not a security gate.

---

## Meta

- **Title:** FailPack — Golden CI packs from agent failures
- **Description:** Capture a coding-agent failure once. Promote it to golden. Replay it on every PR so the same bug cannot quietly come back.
- **OG blurb:** Agent chat is not a test suite. FailPack is.

---

## Hero

**FailPack**

Your agent failed once.  
Make CI remember.

Capture a bad coding-agent session → promote golden assertions → replay on every pull request.  
Ship the memory of the bug, not a Slack thread.

[Get the CLI — free](#quickstart) · [Join the waitlist](#waitlist) · [Personal $19](#pricing)

---

## Problem

Coding agents fail in weird, one-off ways.

Someone pastes a stack trace. Someone “fixes it.” Six weeks later a different run reintroduces the same missing import, wrong path, or silent exit 0.

**Chat history is not a regression suite.**

---

## How it works

1. **Capture** — drop a Claude-Code-like JSONL transcript into FailPack.  
2. **Promote** — mark the session golden; FailPack writes fingerprints, expected error text, and exit code.  
3. **Replay** — CI runs `failpack replay <id>` and fails the build when assertions drift.

Open core. Paid later for private packs and a team dashboard.

---

## Who it’s for

- Solo builders who want failure memory that survives the next agent session  
- Teams that are tired of re-discovering the same agent foot-guns in PR review  
- Anyone shipping agent-assisted code who needs a boring CI signal, not another chat UI

---

## Pricing

| | Open | Personal | Team |
|---|---|---|---|
| Price | $0 | **$19 / mo** | **$79 / mo** |
| Local capture → promote → replay | ✓ | ✓ | ✓ |
| GitHub Action replay | ✓ | ✓ | ✓ |
| Private pack sync | — | ✓ | ✓ |
| Run history | — | basic | full |
| Shared org packs + dashboard | — | — | ✓ |
| Seats / promote audit | — | — | ✓ |

Checkout via merchant of record (**Creem** or **Paddle**). We pick the MoR that can actually settle payouts to our region — including founders who need mainland China–compatible settlement. Do not assume Polar covers that.

---

## Quickstart

```bash
pip install failpack   # or: uv sync && uv run failpack
failpack init
failpack capture path/to/transcript.jsonl
failpack promote <id>
failpack replay <id>   # exit 0 = green, non-zero = regression
```

Pro license check (stub today; gates private sync later):

```bash
export FAILPACK_LICENSE='v1....'
failpack license check
```

---

## Waitlist

**Get Personal / Team when private packs ship.**

Email: `[ your-email@company.com ]`  
→ placeholder form action: `https://example.com/failpack-waitlist` (replace with Buttondown / Loops / Tally / Creem customer portal)

Copy for the button: **Join the waitlist**

Microcopy under the field: No spam. One note when private packs go live. Unsubscribe anytime.

---

## Non-goals (say this out loud)

- Not a security scanner or prompt firewall  
- Not a full agent runtime freeze  
- Not tied to any one agent product install — bring your own transcript fixture  

---

## Footer CTA

Stop relearning the same agent failure.  
**Capture it once. Replay it forever.**

[Star the repo] · [Join the waitlist] · [$19 Personal]
