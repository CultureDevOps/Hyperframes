# OPS-010 — Debian 13 FFmpeg CVE triage and digest-pinned pilot

**Snapshot:** 2026-11-01; reviewed official Debian Security Tracker for
source package `ffmpeg` in **Trixie**. Official package reported:
`7:7.1.5-0+deb13u1`. **Not a CVE-free version**. Source:
https://security-tracker.debian.org/tracker/source-package/ffmpeg

The following is a *selected, workflow-relevant set*, not an exhaustive
count or complete CVE scan. Confirm status/date again before a production
decision. Debian labels many of these “vulnerable (no DSA, postponed)”;
**postponed does not mean fixed**.

| CVE | Affected feature / failure | Trixie 7:7.1.5-0+deb13u1 | Exposure in current HyperFrames path |
|---|---|---|---|
| CVE-2026-107678 | MOV/MP4 PSSH parsing: stack exhaustion / CPU denial of service | vulnerable, postponed | **Directly relevant format:** FFmpeg opens generated MP4 for audio mux; malicious replacement of the intermediate file would increase exposure |
| CVE-2026-70632 | CFHD decoder via crafted AVI: heap out-of-bounds write, possible code execution | vulnerable, postponed | No AVI/CFHD in existing render/mux commands; relevant if importing untrusted media |
| CVE-2026-6385 | MPEG-PS/VOB DVD subtitle parsing: heap out-of-bounds write | vulnerable, postponed | No MPEG-PS or DVD subtitle input in current commands |
| CVE-2026-107697 | HLS child playlist restrictions bypass; accesses forbidden local/protocol resources | vulnerable, postponed | No HLS playlist input in current commands |
| CVE-2026-120210 | IMF ASSETMAP path traversal; local file/network access | vulnerable, no fixed version listed | No IMF package input in current commands |
| CVE-2026-66040 | PNG/APNG encoder metadata: heap out-of-bounds write | vulnerable, postponed | Final mux uses `-c:v copy` and AAC; does not invoke FFmpeg PNG/APNG encoder on these paths |

Individual official tracker details:
https://security-tracker.debian.org/tracker/CVE-2026-107678
https://security-tracker.debian.org/tracker/CVE-2026-70632
https://security-tracker.debian.org/tracker/CVE-2026-6385
https://security-tracker.debian.org/tracker/CVE-2026-107697
https://security-tracker.debian.org/tracker/CVE-2026-120210
https://security-tracker.debian.org/tracker/CVE-2026-66040

**Examples of genuine vendor security fixes:** DSA-6361-1 (2026-06-22)
says `7:7.1.5-0+deb13u1` fixes CVE-2025-22921,
CVE-2026-8461 and CVE-2026-30997 for Trixie.
https://lists.debian.org/debian-security-announce/2026/msg00272.html
These fixes do **not** cover every later/open issue.

## Intended input model / mitigations (not proof of absence)

Current verified workflows generate their own HTML/CSS composition video,
then read the resulting **local MP4** and a **locally synthesized WAV** to
mux the final video: `ffmpeg -i renders/....mp4 -i soundtrack.wav
-map 0:v:0 -map 1:a:0 -c:v copy -c:a aac`. No remote media,
HLS, AVI, DVD subtitle or IMF file is passed deliberately. All jobs run
on disposable GitHub-hosted runners and upload **zero videos**.
However, a compromised dependency or malicious substituted file can
invalidate the trusted-input assumption; containerization mitigates
isolation risks but is not an exploit-proof sandbox. Do not use the
current tooling to decode user-supplied untrusted media until reviewed.

## Immutable OCI source and experiment

Official Docker image `debian:trixie-20261027` is listed by Docker Official
Images and Debian's reproducibility portal:
- https://hub.docker.com/_/debian
- https://github.com/docker-library/official-images/blob/master/library/debian
- https://docker.debian.net/ (2026-10-27 official `amd64` OCI manifest:
  `sha256:e2914ec98e08b24b4cee3cefcb9f90dfb5519f8d215a2ccf0c9a49b10b6e43de`)
- Provenance data recorded in `scripts/debian-trixie-image-lock.json`.

The optional GitHub **PR-only** diagnostic job `probe-debian-ffmpeg`
requests this precise `docker.io/library/debian@sha256:...` digest on a
**standard GitHub-hosted Ubuntu 24.04** runner with no `--privileged`
or self-hosted Docker socket. It verifies the container OS and amd64,
updates only the container's ephemeral signed APT index, and reads
`apt-cache policy ffmpeg`, **without package install, media render,
artifact upload or deployment**. Logs must prove pull success and actual
APT candidate. The OCI digest pins an **amd64 manifest** (not a
multi-architecture tag); SHA256 identifies content but does not by itself
provide publisher signatures or independent supply-chain attestations.
Live APT metadata remains variable, so this is not a complete lock of
the future FFmpeg runtime.

## Decision gate for *future* no-upload rendering pilot

If the digest probe succeeds, verify the candidate's repository
and security-tracker status, then independently review Chrome Headless
Shell dependencies, FFmpeg/library versions, available font packages,
trust chain, architecture and image update cadence. A distinct reviewed
PR-only experiment may install exactly the candidate in a disposable
Debian container and try the three MP4 contracts without upload.
**Do not switch the existing three render workflows, merge, deploy,
publish video or activate paid resources** as part of this lot.
