# Render verification (OPS-010)

The three existing render workflows are intentionally limited to **manual dispatch**
or pushes to **main** with path filters. Branch pushes and pull requests do not
produce video artifacts. The `verify.yml` pull-request workflow runs standard
library Python tests only; it does not install HyperFrames, render, upload,
publish, or deploy any video.

Each render checks its muxed MP4 with:

```bash
python3 scripts/verify_render.py path/to/render.mp4 --seconds 10
# For the MVC explainer: --seconds 35
```

The shared validator uses `ffprobe` to require a nonempty MP4 with 1920x1080
video, 30 fps (tolerance 0.05 fps), AAC audio and an expected duration
(tolerance 0.25 seconds). Errors explicitly identify the mismatched field.

Local tests, without FFmpeg or downloaded dependencies:

```bash
python3 -m unittest discover -s tests -v
```

**Not yet fully reproducible:** `package.json` still specifies
`hyperframes: latest`, there is no committed npm lockfile and render
environments use floating `ubuntu-latest` and system FFmpeg. Pin and test
these dependencies in a separate PR using a known-good render baseline.
Do not merge this PR without considering that changes to the render workflow
files match their main-push path filters and will automatically produce
GitHub Actions video artifacts on merge.
