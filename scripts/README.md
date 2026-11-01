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

Remaining work: complete private local visual review, evaluate the FFmpeg
security-remediation options described below, and review artifact retention.
GitHub Actions are already SHA pinned. No byte-for-byte video reproducibility is claimed.

## CSS-only timeline declaration

Each CSS-only composition's root `<main data-no-timeline>` explicitly opts out of HyperFrames'
JavaScript `window.__timelines` registry because all scene timing uses CSS
keyframe animations. This resolves the observed `missing_timeline_registry`
and `missing_data_no_timeline` diagnostics without altering the storyboard.
The required CI lint will fail if either issue returns.

## Remaining reproducibility caveats

Runner image/library patches, browser download integrity and fonts
remain changeable. GitHub Actions are pinned to full commit SHAs. This lot checks for version drift but does
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

## FFmpeg security review (manual changes, CI-controlled)

**Security notice, reviewed 2026-11-01:** Ubuntu
[USN-8915-1](https://ubuntu.com/security/notices/USN-8915-1), published
2026-10-12, lists Ubuntu 24.04's fixed `ffmpeg` package
`7:6.1.1-3ubuntu5+esm15` via **Ubuntu Pro ESM Apps**. Our reproducible
baseline `7:6.1.1-3ubuntu5` predates that fix. Successful render, a
known package version and an executable SHA256 do **not** mean the baseline
is free of known vulnerabilities. We have not verified any ESM entitlement,
activated Ubuntu Pro or installed a new package. The current security gap
is **unresolved**; do not merge or ship this baseline as a "secure" build.

The small `scripts/ffmpeg-security-policy.json` records the explicitly
known advisory, fixed version, status, review date and **next review due
2026-11-15**. `python3 scripts/audit_ffmpeg_security.py` runs in the
required PR test job; it emits a visible GitHub warning for this risk and
fails if the review is older than 14 days, if the advisory is removed, or
if the package pin drifts from any of the four workflows and
`scripts/check_toolchain.py`. **It is an offline consistency/review gate,
not a live vulnerability scanner**, and passing it does not imply the
FFmpeg package is secure.

For each security review or new Ubuntu USN:
1. Check upstream notices and Ubuntu 24.04 package availability using
   Ubuntu's security pages and `apt-cache policy ffmpeg` on a *temporary
   Ubuntu 24.04 runner*. Verify exact APT package version including epoch,
   archive origin, and whether the update requires ESM Apps or any
   subscription. Do not assume a package listed by a vendor is available
   to GitHub-hosted runners.
2. If the fix is ESM-only, **stop for a separate entitlement/cost and
   deployment decision**. Do not activate Ubuntu Pro, change sources,
   pull binaries from mirrors/PPAs or fall back silently. A supported
   non-paid distribution/runner baseline may be evaluated separately.
3. For an approved available update, use a dedicated PR/commit to update
   **all four** `apt-get install ffmpeg=...` pins, the actual executable
   `FFMPEG_BASELINE` in `check_toolchain.py`, the manifest/advisory and
   tests together. Review linked libav dependency origin/version as well.
   Never use unversioned `apt install ffmpeg` in these render workflows.
4. Re-run the required Python tests, three HyperFrames lints and all
   **three ephemeral real renders** (intro, Nounours, MVC) with MP4 contract
   and exact Chrome/FFmpeg checks. Confirm zero uploaded artifacts.
   Re-review sample frames and audio locally before authorizing
   any manual distribution or merging the Draft PR.

This two-track process preserves a known reproducible CI baseline while
making security debt visible, dated and mandatory to revisit. A new version
must be independently verified, not inferred from this manifest.

## Vendor-supported FFmpeg alternatives (OPS-010)

See [ffmpeg-candidates.md](ffmpeg-candidates.md) for free source options,
unresolved CVE caveats and no-install Ubuntu 24.04/26.04 APT probes.

## Debian 13 security triage and OCI digest probe

See [debian-trixie-risk-review.md](debian-trixie-risk-review.md) and
[`debian-trixie-image-lock.json`](debian-trixie-image-lock.json).
The PR-only Debian job checks official amd64 image digest and live APT
candidate **without installing FFmpeg or rendering media**. Debian's
remaining CVEs are not considered resolved by a pinned container.

## Windows PowerShell: one-command private local render and review

From the root of your local `CultureDevOps/Hyperframes` checkout,
use the new cross-platform script (PowerShell 5.1 or 7+):

```powershell
# One command per composition: render, original sound, MP4 check, contact sheet.
.\scripts\render_and_review.ps1 -Composition intro
.\scripts\render_and_review.ps1 -Composition nounours
.\scripts\render_and_review.ps1 -Composition mvc

# Preview the plan without installing, rendering or writing files.
.\scripts\render_and_review.ps1 -Composition mvc -PlanOnly

# Reuse an existing local final MP4 (review only; no new rendering).
.\scripts\render_and_review.ps1 -Composition mvc -ExistingMp4 "C:\Videos\mvc-explainer.mp4"
```

Prerequisites: **Node.js 22 + npm, Python 3, FFmpeg and FFprobe on PATH**,
and access to the existing repository. The script runs `npm ci` using the
committed lockfile and HyperFrames `lint`, then renders into an ignored
temporary directory within the local checkout, generates the composition's
original soundtrack, muxes AAC, moves the final MP4 to a private directory
**outside the public repository**, verifies the MP4 contract and generates
the 3×3 contact sheet with `private_visual_review.py`. Intermediate
raw MP4, WAV and mux files are deleted even if a stage fails.

Default output: `~/.hyperframes-private-review/`; use
`-OutputDirectory "D:\Private\Hyperframes"` for another private local folder.
The final video is uniquely named, so prior reviews aren't overwritten. The
contact sheet and manifest live in a distinct `review-.../` child folder.
Inspect the local final MP4 for sound and motion: a contact sheet cannot
validate audio balance or pacing. On Windows **verify inherited NTFS ACLs**
restrict the output, and avoid folders synced to shared cloud storage.

Options: `-SkipInstall` reuses previously installed locked `node_modules`;
`-ExistingMp4` validates and reviews an existing final MP4 without requiring
Node or running HyperFrames; `-PlanOnly` has no side effects. On Windows the
script invokes `npm.cmd`/`npx.cmd` to avoid PowerShell execution-policy
problems with `npm.ps1`/`npx.ps1`, and uses the Python launcher `py -3`
when available.

**Privacy boundary:** no media upload, GitHub artifact, release, network
publisher or automatic sharing is called. Local rendering/review and media
storage are private by design, **but initial `npm ci` and HyperFrames Chrome
bootstrap can download dependencies over the Internet**. This is *not* a
guarantee of offline execution or of encrypted local storage. For a
pre-provisioned setup, `-SkipInstall` avoids npm installation but the
HyperFrames browser cache still needs to be present.

The PR CI exercises `-PlanOnly` and performs a full PowerShell intro
render/mux/validate/contact-sheet run on a disposable GitHub-hosted runner
without uploading the video or review PNGs. It checks that staging files
are cleaned up before discarding the runner. This does not substitute for a
human local review on Windows and does not remove the known FFmpeg security
debt described above. No new runner, package subscription, production deploy,
video publication or merge is authorized by this step.

## Windows NTFS private output and native Windows CI (OPS-010)

The PowerShell local renderer now **fails closed** when a Windows output
directory has inherited/broad ACLs. When creating a *new* leaf folder on a
fixed local NTFS volume, \`scripts/private_output_acl.ps1\` disables
inheritance and grants FullControl only to the current Windows user and
the SYSTEM service SID. It re-reads and checks the ACL before rendering.
An **existing** directory is validated, never silently modified. A folder
with an Everyone/Users ACE, unprotected inheritance, a reparse-point
(junction/symlink) ancestor, a UNC path or a non-fixed/non-NTFS volume is
rejected. The parent directory must already exist.

For example, choose a brand-new child of an existing private local folder:

\`\`\`powershell
.\scripts\render_and_review.ps1 -Composition mvc -OutputDirectory "$HOME\Hyperframes-Review-Private"
\`\`\`

Windows local output uses **Copy-Item** (not same-volume Move-Item) from
the staging directory, so the final MP4 inherits destination NTFS permissions;
it then checks the copied MP4 ACL. Linux retains its existing move path.
Untrusted existing folders need a *new* private output path rather than
automatic ACL weakening/rewriting. Admins or the filesystem owner may still
be capable of changing permissions, and NTFS ACLs are **not encryption**.
Do not use shared or cloud-synced locations. No media is sent to GitHub.

PR CI runs **native Windows PowerShell 5.1 and PowerShell 7** on a disposable
Windows GitHub-hosted runner, with only \`-PlanOnly\` and an ACL regression
test in a freshly created temporary directory. That job verifies restricted
directory and child-file permissions, rejects a synthetic overly permissive
directory without mutating it, and rejects UNC paths. It **does not run a
real media render on Windows**, install local FFmpeg or access the user's PC.
The previously validated full PowerShell media render remains on an ephemeral
Linux runner.
