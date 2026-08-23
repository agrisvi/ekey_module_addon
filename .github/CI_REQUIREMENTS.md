# CI requirements — the add-on store repository

One of three repositories that make up the ekey module. The daemon's own repository is not
public, so nothing here relies on being able to read it. The first question is the same one
asked of the other two, and here the answer is different in an interesting way:

> *Do the automatic checks need a working connection to the scanner, or a Home Assistant?*

**No — but they do need the internet, and that is the point of them.** There is no code in
this repository to test. There is `repository.yaml`, one add-on's `config.yaml`, and two
documents. What the checks verify is not behaviour but *agreement*: that the version this
repository advertises matches an image that actually exists in the registry a user's
Supervisor will pull from.

## What was found

**This repository had no GitHub Actions at all.** So nothing was failing — and nothing was
being checked either, which for a repository whose entire job is to be correct metadata is
the more expensive of the two. Everything here is consumed by the Supervisor on someone
else's machine, at install time, and every mistake surfaces there as an error that names
`ghcr.io` rather than the field that was wrong.

One check was added, in `validate.yml`, calling `.github/scripts/validate_store.py`.
Verified against this repository as it stands: **0 failures, 0 warnings**, with all three
published images confirmed present. Verified against deliberately broken fixtures too, so
the checks are known to fire rather than merely to pass.

## Part 1 — What the checks require

- **R1 — Runner.** `ubuntu-latest`, GitHub-hosted. Python 3.13 and PyYAML; the registry
  query is plain `urllib`.
- **R2 — Outbound network to `ghcr.io`.** The registry check is the reason this workflow
  earns its keep, and it is the one thing here that cannot be done offline. `--offline`
  skips it for local runs.
- **R3 — The GHCR package must be anonymously readable.** Not asserted as a failure,
  because a private package and a missing tag are indistinguishable from outside — the run
  reports HTTP 401/403 as a warning saying exactly that. It matters anyway: **the Supervisor
  has no registry credentials**, so a private package cannot be installed by anyone. All
  three images are currently public, which is the correct state.
- **R4 — Nothing is checked by running it.** No Supervisor, no Home Assistant, no add-on
  container is started. That is a deliberate limit, not an omission: see part 3.

## Part 2 — What is fatal and why

Each of these is a way for a user's install to fail while every file here still reads
correctly.

- **F1 — `repository.yaml` present, parsing, with `name`, `url`, `maintainer`.** Without the
  file the Supervisor rejects the whole repository: "Add repository" reports no add-ons
  whatever the folders contain.
- **F2 — At least one `*/config.yaml`.** The Supervisor treats every top-level directory
  holding one as an add-on. None means this repository offers nothing.
- **F3 — `name`, `version`, `slug`, `arch` present.**
- **F4 — `version` must be a YAML *string*.** `version: 1.20` unquoted is the float `1.2`,
  and the trailing zero is gone before anything downstream sees it. The publishing workflow
  in the source repository reads this field with a `sed` that matches quoted values only, so
  an unquoted version there yields an empty string and stops the build; here it would
  silently become the wrong image tag.
- **F5 — `image` present.** Specific to this repository: it carries no Dockerfile and no
  sources, so without a prebuilt image the Supervisor tries to build from sources that were
  deliberately never published. The whole `libekey_scanner.so` split exists so those sources
  never reach a user's machine.
- **F6 — `image` keeps the literal `{arch}`, and is all lowercase.** The Supervisor
  substitutes `{arch}` per machine, so hardcoding one architecture makes the add-on
  uninstallable on the others; registries reject a mixed-case path, and a GitHub owner name
  is not guaranteed to be lowercase.
- **F7 — every `arch` is one the Supervisor knows** (`aarch64`, `amd64`, `armhf`, `armv7`,
  `i386`). An unknown one is never matched, so the add-on is invisible rather than broken —
  the hardest kind of failure to diagnose from a bug report.
- **F8 — `<image>:<version>` exists in the registry, for every listed arch.** The one that
  actually bites. The Supervisor pulls exactly that tag: publish a different one and the
  install fails on a manifest that does not exist. **Bump `version` in `config.yaml` only
  after publishing an image for it — in that order.**

Advisory, not fatal: a `slug` that disagrees with its directory name (the Supervisor
identifies the add-on by slug and the folder name is free, but every path in the docs and
the source repository assumes they agree), and a package that is not anonymously readable.

## Part 3 — What is deliberately NOT checked

Worth writing down so the gaps are known rather than assumed away.

- **That the image actually runs.** Pulling and starting the add-on container would need a
  Supervisor, or at least a `docker run` with the add-on's environment faked. The image is
  built and its build is gated in the source repository; this repository only asserts that
  the tag the Supervisor will ask for is there.
- **That `config.yaml` matches the source repository's copy.** It is copied here verbatim by
  a sync script in the (non-public) source repository, and the two are byte-identical as of
  this writing — but only that side can check it, because only that side holds both files. A
  divergence would show up here as a version pointing at an image nobody published, which
  F8 does catch.
- **The add-on's option schema.** A `config.yaml` whose `options`/`schema` disagree is
  rejected by the Supervisor at install time and nothing here would notice. The community
  `frenck/action-addon-linter` action covers this and could be added; it was left out
  deliberately rather than overlooked, because it builds a Dockerfile on every run and this
  repository's failure modes are all in the four fields above. Add it if the options grow.

## Part 4 — IF a hardware or Supervisor test is ever wanted

Nothing here needs it today. If it is ever added, all of the following apply — the same
rules the other two repositories follow:

- A **separate** workflow, and **not** a required status check: hardware that is unplugged
  or mid-reflash must never block a merge.
- A **self-hosted** runner, registered to this repository, that a fork PR can never reach.
  A self-hosted runner reachable by fork PRs is arbitrary code execution on the machine
  wired to the door hardware. Practically: `workflow_dispatch` and pushes to `main` only,
  behind an `environment:` with a required reviewer.
- `concurrency: group: hil, cancel-in-progress: false` — one device, one job. Two jobs
  sharing one bus produce failures that look like protocol bugs.
- Timeouts on every device interaction and `timeout-minutes` on the job, so a hung read
  cannot hold the single-device group for hours.
- Secrets from repository secrets or the runner's filesystem, never the repository — and
  cleaned up in a step that runs on failure too, because a self-hosted runner's workspace
  persists between runs.
- Probe the device first and fail with `not present at <path>` before any test runs, so
  absent hardware can never be reported as a regression.
- **The door output goes to an LED or an opto input the job can read back, never to a real
  lock**, and the device under test is a dedicated unit whose user database is expendable.
  CI must not be able to unlock a door.
