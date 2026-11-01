# OPS-010 — GitHub Actions pins (reviewed 2026-11-01)

Five public `.github/workflows/*.yml` files use three official GitHub Actions at full commit SHAs, recorded in [actions-lock.json](actions-lock.json): `actions/checkout`, `actions/setup-node` and `actions/setup-python`.

The offline `tests/test_actions_pins.py` job runs on pull requests through `ops010-tooling.yml` and fails closed on unknown actions, Docker/local actions, floating refs, an unexpected SHA, lack of restricted permissions or artifact uploads. The list of workflows is discovered automatically; new workflows must conform.

The original Draft PR #1 manifest allowed `actions/upload-artifact`; that entry has been deliberately **deleted**. PR #3 previously removed media uploads from live workflows. Nothing in this lot renders or publishes media.

The SHAs and official upstream version references were reviewed on 2026-11-01. Immutable action refs do **not** pin the GitHub runner image, Ubuntu package repositories, FFmpeg, Chrome, or a supply-chain signature. To change a pin, first review the official action release and commit, then update YAML and the allowlist together in a PR.

This is a CI integrity check, **not** FFmpeg CVE remediation.
