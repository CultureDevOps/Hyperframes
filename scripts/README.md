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
- FFmpeg is requested as **`ffmpeg=6.1.1-3ubuntu5`** via Ubuntu 24.04
  apt, then the validator checks both FFmpeg and FFprobe versions. If this
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
