# ekey module — Home Assistant add-on repository

The backend for the **ekey module fingerprint scanner** (OEM version), packaged as a
Home Assistant add-on. It talks to the scanner over RS485 and serves an HTTP/SSE API
that the [ekey module App](https://github.com/agrisvi/ekey_module_app) integration
consumes, plus its own management pages in the Home Assistant sidebar.

## Install

1. **Settings → Add-ons → Add-on Store → ⋮ → Repositories**
2. Add `https://github.com/agrisvi/ekey_module_addon`
3. Install **ekey module Daemon** from the list that appears
4. **Configuration** tab → pick your RS485 converter from the `serial_port` dropdown →
   **Save**. The add-on will not start without one: on this product the port is an
   installation setting, not something the web page changes.
5. **Start**, then read the **Log** tab. Note the `App API token` line — the
   integration needs it.
6. **ekey** appears in the sidebar and opens the access log. **Settings** in its header
   opens the admin page. No token is needed for either; ingress requests are already
   authenticated by Home Assistant.

Then install the [ekey module App](https://github.com/agrisvi/ekey_module_app)
integration through HACS and point it at **Local — ekey-ha-daemon on this host
(HTTP)**, host `127.0.0.1`, port `8080`, with the token from step 5.

The add-on's own **Documentation** tab (the full version of
[`ekey_ha_daemon/DOCS.md`](ekey_ha_daemon/DOCS.md)) covers the options, the sidebar
page, storage and troubleshooting.

Nothing is compiled on your machine. The Supervisor pulls a prebuilt image for your
architecture — `aarch64`, `armv7` or `amd64` — so installing on a Raspberry Pi 3B+ is a
download rather than the 15–30 minute gcc run a local build would be.

## Why this repository holds no source

It contains four files: `repository.yaml`, which is what makes the git URL usable as an
add-on repository at all, and then `ekey_ha_daemon/config.yaml` plus its `DOCS.md` —
the add-on itself and the text the Supervisor renders on its **Documentation** tab —
and this README. That is the whole add-on as far as Home Assistant is concerned: with
`image:` set the Supervisor pulls the container and never looks at a `Dockerfile` or a
source tree, so shipping them here would serve nobody.

It is also the point. The scanner driver is proprietary, and a locally-built add-on
copies its plaintext sources onto every user's device in order to compile them there.
Distributing a built image instead means the sources stay where they are built, and what
users receive is the compiled artefact — faster to install *and* the version that does
not hand out the code.

The source, the `Dockerfile` and the image workflow live in a private repository. This
one is the shop window: public, so Home Assistant can read it, and carrying nothing that
needs to be private.

## Updating

The Supervisor offers add-on updates when the `version:` here changes. Each version has
a matching image tag published before it lands, so an update is a pull, not a build.

## Configuration

| Option | Default | What it does |
| --- | --- | --- |
| `serial_port` | *(empty)* | The RS485 device. Required — pick it from the dropdown. Internal (non-USB) ports are listed too. |
| `api_bind_ip` | *(empty)* | Optionally also serve the REST API on this address. `/api/v1` is **unauthenticated**, so only set this on a trusted network. |
| `log_request_bodies` | `false` | Write request bodies to the add-on log. Off by default and worth leaving off: they carry people's names and fingerprint template hex, and add-on logs go into every support bundle. |

## Two things that are easy to get wrong

**One daemon per scanner.** The daemon is an RS485 bus master and the scanner couples to
a single master. Running this add-on and another daemon against the same scanner makes
the second re-couple it mid-session, and pairing fails with *"Failed to obtain persistent
key"*.

**The serial port is set here, not in the web page.** The ekey page has a port picker on
other backends; the add-on starts the daemon with `--no-serial-select` so the page shows
which port is in use and offers no control to change it. The Supervisor owns that
setting — it is what maps the device into the container in the first place — so a change
made in the page could not take effect anyway.

## Issues

<https://github.com/agrisvi/ekey_module_addon/issues>
