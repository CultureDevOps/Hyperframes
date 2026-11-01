# Reproducible render contract (OPS-010)

The three render workflows are **workflow_dispatch only**. They are not
triggered by pushes, merges or pull requests. Video artifact upload is disabled
by default: manual dispatch requires `upload_artifact: true` to enable
upload. That choice must be separately authorized. When enabled, uploads are
limited to the verified final MP4 and have a three-day retention window.
The PR validation workflow first runs Python unit tests, a locked-CLI check
and **required `hyperframes lint`** for all three CSS-only compositions, then runs
**intro (10 s), Nounours (10 s), MVC (35 s)** disposable renders with music and ffprobe checks on
a disposable GitHub-hosted runner. The smoke job runs only for pull requests,
does not upload or retain video, and has no deployment or external publishing
steps. This verifies technical render output, **not visual composition quality**.

## Toolchain reference

- `hyperframes@0.8.221` verified in the successful 2026-10-30 intro/MVC jobs;
  now **exact-pinned** in `package.json`.
- npm lockfile version 3 checked in. All 127 package entries were resolved by
  npm from the public npm registry in PR CI and include integrity hashes for
  downloadable packages. Both PR smoke and renders install using `npm ci`.
- Node.js 22 on GitHub-hosted `ubuntu-24.04` runners.
- `HYPERFRAMES_NO_UPDATE_CHECK=1` prevents the CLI update check/auto-install.
- FFmpeg is requested as **`ffmpeg=7:6.1.1-3ubuntu5`** via Ubuntu 24.04
  apt (Debian package epoch `7:`), then the validator checks both FFmpeg and FFprobe versions. If this
  apt version disappears from the mirror, the CI fails instead of drifting.
- HyperFrames installs its pinned Chrome Headless Shell binary; after each
  ephemeral render the validator checks the executable's version equals
  **`152.0.7977.30`**, and its cache path matches. This validates an
  observed runtime version, not the remote download checksum.

Merging this PR will **not** trigger a render on `main` because the three
render workflows have no `push` or `pull_request` trigger. A manual dispatch
is still an explicit operation and artifact upload remains opt-in. Merging
is separately permissioned. The PR smoke checks MP4 technical properties; it does not prove visual pacing.

## Validate

```bash
npm ci --no-audit --no-fund
python3 -m unittest discover -s tests -v
python3 scripts/verify_render.py path/to/render.mp4 --seconds 10
# For the MVC explainer: --seconds 35
```

The shared `ffprobe` check requires nonempty MP4 output with 1920x1080 video,
30 fps (+/- 0.05), AAC audio and the intended 10s or 35s duration (+/- 0.25s).
Failures identify the violated contract.

Remaining work: manually review visual pacing using an approved non-publication method,
consider digest-pinning GitHub Actions and an FFmpeg/Chrome distribution strategy,
and review artifact retention. No byte-for-byte video reproducibility is claimed.

## CSS-only timeline declaration

Each CSS-only composition's root `<main data-no-timeline>` explicitly opts out of HyperFrames'
JavaScript `window.__timelines` registry because all scene timing uses CSS
keyframe animations. This resolves the observed `missing_timeline_registry`
and `missing_data_no_timeline` diagnostics without altering the storyboard.
The required CI lint will fail if either issue returns.

## Remaining reproducibility caveats

Runner image/library patches, browser download integrity, fonts and GitHub
Actions tag refs remain changeable. This lot checks for version drift but does
not establish bit-identical output. It avoids Docker/privileged runners,
retains only logs (no PR video uploads), and does not deploy or publish video.

## Immutable GitHub Actions pins

All `actions/checkout`, `actions/setup-node`, `actions/setup-python` and
`actions/upload-artifact` invocations use complete, immutable **40-hex commit SHAs**,
rather than movable `@v4` or `@v5` aliases. Their exact SHA values were
checked on **2026-11-01** against the official `actions/*` repositories via
GitHub's tag-ref API; `scripts/actions-lock.json` records the major aliases and
resolved commit identifiers. `tests/test_actions_pins.py` rejects unapproved
or floating `uses:` references across all workflows.

When updating, review the upstream action release, resolve its new official
commit SHA, update both the YAML uses and manifest, and rerun tests/CI. This
locks action source revisions; it does **not** lock GitHub runner images, installed
system packages or browser download hashes, nor prove action-code safety.

## Private on-device visual review (no publishing)

**Important:** this GitHub repository is **public**. GitHub Actions videos or
screenshots attached as artifacts, pull-request comments, releases or commit
files are **not private** and MUST NOT be used as visual review material.
The existing CI smoke runs discard all videos when the ephemeral runner ends.

To inspect one video, obtain or render the final MP4 **locally on your own
workstation**, including its original soundtrack. Nothing in CI can be
downloaded later because no MP4 was uploaded. Use the corresponding manual
render workflow steps locally, with `npm ci` and the matching soundtrack
generator, but never use GitHub Actions upload as a transport.

Then run this entirely local tool from the repository root:

```powershell
# PowerShell: example with an MP4 already rendered and muxed on this PC
py -3 scripts/private_visual_review.py "C:\Videos\mvc-explainer.mp4" --seconds 35
# Intro and nounours: --seconds 10
```

The tool requires local `ffmpeg` and `ffprobe`. It validates the same MP4
contract and extracts nine frames at 5–95% of the duration into a 3×3
contact sheet under `~/.hyperframes-private-review/review-<UTC>-<random>/`,
with a source SHA-256 and timestamp fractions in `manifest.json`. The output
is **never** created inside this Git repository. On POSIX the private folder
must have mode 0700 and files use restrictive permissions. On Windows,
**verify that inherited NTFS ACLs restrict the output directory**; `chmod`
does not establish Windows confidentiality.

Review the contact sheet for crops and legibility, then play the original
MP4 locally for motion, sound levels, timing and whether the punchline lands.
Do not share the MP4 or screenshot through public GitHub, CI logs or cloud
storage. The script does not upload or send data anywhere.

## Binary provenance decision

On Ubuntu, apt validates signed repository `InRelease` metadata which pins
`Packages` hashes and in turn the `.deb` checksums; this provides a stronger
origin chain than comparing `ffmpeg -version` alone. Ubuntu documents the
mechanism: https://documentation.ubuntu.com/security/software-integrity/archive-verification/ .
A fixed apt version can disappear from current repositories; Ubuntu Snapshot
is a potential future frozen source, requiring separate review.

Chrome for Testing provides official **version/platform/download URLs**:
https://github.com/GoogleChromeLabs/chrome-for-testing . A version string and
path are not themselves a cryptographic authenticity check. For the current
HyperFrames-managed download, CI's intro smoke logs **SHA-256 of the installed
FFmpeg, FFprobe and Chrome executables** (hashes only; no media). These are
auditable *observed fingerprints*, **not** vendor-signed or independently
trusted digests. Do not promote them into trust anchors without reviewing
the archive origin and binary signing/integrity evidence. No automatic browser
upgrade, binary replacement or new paid resource is performed.
