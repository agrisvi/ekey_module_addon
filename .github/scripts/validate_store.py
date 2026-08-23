#!/usr/bin/env python3
"""Validate this add-on repository the way the Supervisor and a user's install will.

This repository carries no Dockerfile and no sources — only `repository.yaml` and one
add-on directory holding a `config.yaml`. Everything that can go wrong here therefore goes
wrong in one of two ways, and neither produces a useful error on the user's machine:

  * the Supervisor rejects the repository or the add-on outright, because a field it needs
    is missing, or is the wrong YAML type;
  * the add-on appears in the store, the user clicks install, and the pull fails because
    `<image>:<version>` does not exist in the registry. The error names the registry, not
    the mistake, and the mistake is always the same one: `version` in config.yaml was
    changed without publishing an image for it, or an image was published under a tag
    nobody asked for.

Both are checked below. Run it locally exactly as CI does:

    python .github/scripts/validate_store.py            # includes the registry check
    python .github/scripts/validate_store.py --offline   # skips it

Needs PyYAML and nothing else.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]

# The Supervisor's own vocabulary. An arch outside this set is silently never matched, so
# the add-on is invisible on every machine rather than broken on one.
KNOWN_ARCHES = {"aarch64", "amd64", "armhf", "armv7", "i386"}

errors: list[str] = []
warnings: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)
    print(f"  FAIL {msg}")


def warn(msg: str) -> None:
    warnings.append(msg)
    print(f"  WARN {msg}")


def ok(msg: str) -> None:
    print(f"  ok   {msg}")


def load_yaml(path: Path):
    try:
        with path.open(encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as err:
        fail(f"{path.relative_to(REPO)} does not parse: {err}")
        return None


# --------------------------------------------------------------- repository.yaml
def check_repository() -> None:
    print("repository.yaml:")
    path = REPO / "repository.yaml"
    if not path.is_file():
        fail("repository.yaml is missing — the Supervisor rejects the whole repository "
             "and 'Add repository' reports no add-ons whatever the folders contain")
        return
    data = load_yaml(path)
    if not isinstance(data, dict):
        fail("repository.yaml is not a mapping")
        return
    for field in ("name", "url", "maintainer"):
        if not data.get(field):
            fail(f"repository.yaml has no '{field}'")
        else:
            ok(f"{field}: {data[field]!r}")


# -------------------------------------------------------------------- config.yaml
def check_addon(config_path: Path) -> list[tuple[str, str]]:
    """Validate one add-on. Returns the (image, tag) pairs its install will pull."""
    directory = config_path.parent
    print(f"\n{directory.name}/config.yaml:")
    data = load_yaml(config_path)
    if not isinstance(data, dict):
        fail(f"{directory.name}/config.yaml is not a mapping")
        return []

    for field in ("name", "version", "slug", "arch"):
        if not data.get(field):
            fail(f"{directory.name}: no '{field}'")

    version = data.get("version")
    slug = data.get("slug")

    # `version: 1.2` unquoted is a FLOAT to YAML, and the trailing zero of 1.20 is gone
    # before anything downstream sees it. The publishing workflow in the source repo reads
    # this field with a sed that matches quoted values only, so an unquoted version there
    # yields an empty string and the build stops; here it would silently become the wrong
    # image tag. Quoting it is the fix in both places.
    if version is not None and not isinstance(version, str):
        fail(f"{directory.name}: version is {type(version).__name__} "
             f"({version!r}) — quote it in the YAML, the Supervisor pulls it as a tag")
        version = None
    elif version:
        ok(f"version: {version!r}")

    if slug and slug != directory.name:
        # Not fatal: the Supervisor identifies the add-on by slug, and the folder name is
        # free. But every path in the docs, the source repo and DOCS.md assumes they agree,
        # so a mismatch is a trap for the next person rather than a bug today.
        warn(f"{directory.name}: slug is {slug!r}, which does not match the directory name")

    arches = data.get("arch") or []
    if not isinstance(arches, list):
        fail(f"{directory.name}: arch must be a list")
        arches = []
    unknown = [a for a in arches if a not in KNOWN_ARCHES]
    if unknown:
        fail(f"{directory.name}: unknown arch {unknown} — an add-on listing an arch the "
             f"Supervisor does not know is invisible, not broken")
    elif arches:
        ok(f"arch: {arches}")

    # `image:` is optional for add-ons in general and MANDATORY here: this repository
    # contains no Dockerfile, so without it the Supervisor tries to build from sources that
    # were deliberately never published, and the install fails with a build error.
    image = data.get("image")
    if not image:
        fail(f"{directory.name}: no 'image' — this repository ships no Dockerfile, so a "
             f"local build has nothing to build. The Supervisor needs a prebuilt image.")
        return []
    if "{arch}" not in image:
        fail(f"{directory.name}: image {image!r} does not contain the literal '{{arch}}' — "
             f"the Supervisor substitutes it per machine, and hardcoding one architecture "
             f"makes the add-on uninstallable on the others")
        return []
    if image != image.lower():
        fail(f"{directory.name}: image {image!r} is not lowercase — registries reject a "
             f"mixed-case image path, and a GitHub owner name is not guaranteed lowercase")
        return []
    ok(f"image: {image}")

    if not version or not arches:
        return []
    return [(image.replace("{arch}", arch), version) for arch in arches]


# ------------------------------------------------------------------ the registry
def registry_status(image: str, tag: str) -> tuple[int, str]:
    """HTTP status for a manifest, anonymously. (status, detail)"""
    # ghcr.io hands out a pull token to anyone for a public package; for a private one it
    # hands out a token that is then refused, which is why 401/403 has to be told apart
    # from 404 below.
    if not image.startswith("ghcr.io/"):
        return (0, "not a ghcr.io image — no anonymous check available")
    repo = image[len("ghcr.io/"):]
    try:
        with urllib.request.urlopen(
            f"https://ghcr.io/token?scope=repository:{repo}:pull&service=ghcr.io",
            timeout=30,
        ) as response:
            token = json.load(response).get("token", "")
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as err:
        return (0, f"could not obtain a pull token: {err}")

    request = urllib.request.Request(
        f"https://ghcr.io/v2/{repo}/manifests/{tag}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": ", ".join([
                "application/vnd.oci.image.manifest.v1+json",
                "application/vnd.oci.image.index.v1+json",
                "application/vnd.docker.distribution.manifest.v2+json",
                "application/vnd.docker.distribution.manifest.list.v2+json",
            ]),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return (response.status, "")
    except urllib.error.HTTPError as err:
        return (err.code, err.reason or "")
    except (urllib.error.URLError, OSError) as err:
        return (0, str(err))


def check_registry(pulls: list[tuple[str, str]]) -> None:
    print("\npublished images:")
    if not pulls:
        warn("nothing to check — an earlier failure means the image list is unknown")
        return
    for image, tag in pulls:
        status, detail = registry_status(image, tag)
        if status == 200:
            ok(f"{image}:{tag} exists")
        elif status == 404:
            fail(f"{image}:{tag} does NOT exist. The Supervisor pulls exactly this tag, so "
                 f"the add-on cannot install. Bump 'version' in config.yaml only after "
                 f"publishing an image for it — in that order.")
        elif status in (401, 403):
            # Not a failure: it means the package is private, which is a real problem for
            # users but not one this check can distinguish from a missing tag.
            warn(f"{image}:{tag} is not anonymously readable (HTTP {status}). Either the "
                 f"package is private — in which case the Supervisor cannot pull it either, "
                 f"since it has no credentials — or the tag is absent. Make the GHCR "
                 f"package public to tell these two apart.")
        else:
            warn(f"{image}:{tag} could not be checked (HTTP {status} {detail})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true",
                        help="skip the registry check (no network)")
    args = parser.parse_args()

    check_repository()

    configs = sorted(REPO.glob("*/config.yaml"))
    if not configs:
        fail("no */config.yaml — the Supervisor treats every top-level directory holding "
             "one as an add-on, so this repository offers nothing")
    pulls: list[tuple[str, str]] = []
    for config in configs:
        pulls += check_addon(config)

    if args.offline:
        print("\npublished images:\n  --  skipped (--offline)")
    else:
        check_registry(pulls)

    print(f"\n{len(errors)} failures, {len(warnings)} warnings")
    for warning in warnings:
        print(f"  warning: {warning}")
    for error in errors:
        print(f"  failure: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
