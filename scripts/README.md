# Reproducible render contract (OPS-010)

The three existing render workflows are intentionally limited to manual dispatch
or pushes to **main** with path filters. Branch pushes and pull requests do not
render or upload videos. The `verify.yml` workflow runs tests and installs the
locked CLI for a no-video smoke test. It never invokes a render command or
uploads artifacts.

## Toolchain reference

- `hyperframes@0.8.221` verified in the successful 2026-10-30 intro/MVC jobs;
  now **exact-pinned** in `package.json`.
- npm lockfile version 3 checked in. All 127 package entries were resolved by
  npm from the public npm registry in PR CI and include integrity hashes for
  downloadable packages. Both PR smoke and renders install using `npm ci`.
- Node.js 22 on GitHub-hosted `ubuntu-24.04` runners.
- `HYPERFRAMES_NO_UPDATE_CHECK=1` prevents the CLI update check/auto-install.
- The observed baseline FFmpeg is `6.1.1-3ubuntu5`, and Headless Chrome was
  `152.0.7977.30`. Their system/binary versions are **not locked** here.

The render workflow files and both npm manifests match the `main` push path
filters. **Merging this PR can automatically trigger all three render jobs** and
upload their videos as GitHub Actions artifacts. Merge/publication need separate
authorization; a green no-video PR smoke test does not prove visual output.

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

Remaining work: validate a real render/visual pacing with the pinned toolchain,
consider digest-pinning GitHub Actions and an FFmpeg/Chrome distribution strategy,
and review artifact retention. No byte-for-byte video reproducibility is claimed.
