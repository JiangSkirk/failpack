# FailPack monetization

Working notes for packaging FailPack (Orin Replay) as a paid product. The open CLI stays useful; money sits on private packs + team UX.

## Landing copy (draft)

### Headline

**Your agent failed once. Make sure it fails the same way in CI — or not at all.**

### Subhead

FailPack turns a coding-agent failure session into a golden regression pack: capture the transcript, promote assertions, replay them on every PR. Ship the memory of the bug, not vibes.

### Problem

Coding agents fail in weird, one-off ways. You paste a stack trace in Slack, someone “fixes it,” and six weeks later a different agent reintroduces the same broken import / wrong path / silent exit 0. Chat history is not a test suite.

### Product

1. **Capture** — drop a Claude-Code-like JSONL transcript into FailPack.
2. **Promote** — mark the session golden; FailPack writes fingerprints + expected error signals.
3. **Replay** — CI runs `failpack replay <id>` and fails the build on drift.

### Who pays

- Solo builders who want private packs and history → **Personal**.
- Teams that want shared golden packs and a dashboard → **Team**.

### CTA

Start free with the open CLI. Upgrade when packs need to leave your laptop.

---

## Pricing stub

| Plan | Price | Includes |
|---|---|---|
| **Open** | $0 | Local CLI, public fixtures, GitHub Action replay |
| **Personal** | **$19 / month** | Private pack sync, encrypted remote store, basic run history |
| **Team** | **$79–149 / month** | Shared org packs, dashboard, seats, audit of who promoted golden |

Annual discount later (e.g. ~2 months free). Team price band: start at $79 for small orgs; $149 when dashboard + seats matter.

**What we do not charge for (v0 narrative):** the core capture/promote/replay loop in open source.

---

## Checkout / merchant of record

Planned MoR options:

- **[Creem](https://www.creem.io/)** — evaluate for global checkout + payout fit.
- **[Paddle](https://www.paddle.com/)** — established MoR (tax/VAT handled); good default for SaaS.

### Mainland China payout note

**Do not assume Polar (or any single MoR) can pay out cleanly to mainland China.** Before locking billing:

1. Confirm the MoR supports your entity / personal payout region.
2. Confirm currency settlement and KYC requirements.
3. Keep Creem **and** Paddle on the shortlist until one clears payout in production.

FailPack’s path to money is **private packs + team dashboard**, billed through a MoR that can actually settle — not through hope that a US-centric creator payout tool covers CN founders.

---

## Packaging narrative (internal)

- Free CLI = top-of-funnel and CI credibility.
- Paid = storage, sync, org permissions, dashboard charts (“which golden packs failed this week”).
- Never position FailPack as a security product; security buyers churn when they discover it is regression memory.
