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
5. **Start**, then read the **Log** tab. `API token handed to Home Assistant (add-on
   discovery)` means the integration will receive the token by itself.
6. Install the [ekey module App](https://github.com/agrisvi/ekey_module_app) integration
   (1.3.2 or later) through HACS and restart Home Assistant. **Settings → Devices &
   services** then shows **"ekey add-on found"** — press **Submit**. There is no token to
   copy: the add-on hands it over through the Supervisor, and hands over a new one
   whenever you regenerate it.
7. Open the pages from the integration's **ekey** sidebar panel: choose the add-on's
   scanner under **Scanner or storage**. **Settings** in the page's header opens the
   admin page. No token is needed; ingress requests are already authenticated by Home
   Assistant. The add-on's own **ekey daemon** sidebar entry (Info tab → "Show in
   sidebar") still works but is no longer needed.

With an integration older than 1.3.2, add it by hand instead: **Local — ekey-ha-daemon on
this host (HTTP)**, host `127.0.0.1`, port `8080`, and the token from the log's
`App API token` line (also in `/data/ekey/app/token`).

The add-on's own **Documentation** tab (the full version of
[`ekey_ha_daemon/DOCS.md`](ekey_ha_daemon/DOCS.md)) covers the options, the sidebar
page, storage and troubleshooting.

Nothing is compiled on your machine. The Supervisor pulls a prebuilt image for your
architecture — `aarch64` or `amd64` — so installing on a Raspberry Pi is a download
rather than the 15–30 minute gcc run a local build would be. A 64-bit OS is required;
32-bit `armv7` is no longer built, following Home Assistant's deprecation of it.

## Why this repository holds no source

It contains only what the Supervisor reads from an add-on directory: `repository.yaml`,
which is what makes the git URL usable as an add-on repository at all, and in
`ekey_ha_daemon/` the add-on itself (`config.yaml`), the text of its **Documentation**
tab (`DOCS.md`), the notes shown when an update is offered (`CHANGELOG.md`) and the
option labels of its **Configuration** tab (`translations/en.yaml`) — plus this README.
That is the whole add-on as far as Home Assistant is concerned: with
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
What changed is in [`ekey_ha_daemon/CHANGELOG.md`](ekey_ha_daemon/CHANGELOG.md), which
the Supervisor also shows next to the update.

The add-on, the [ekey module App](https://github.com/agrisvi/ekey_module_app)
integration and the ekey ESP32 firmware share one version number since 1.3.2, so the
same number means the same release on every side.

## Configuration

| Option | Default | What it does |
| --- | --- | --- |
| `serial_port` | *(empty)* | The RS485 device. Required — pick it from the dropdown. Internal (non-USB) ports are listed too. |
| `allow_external` | `false` | Allow connections from other machines on your network. `/api/v1` is **unauthenticated** unless `require_token` is on, so only tick this on a trusted network. |
| `api_bind_ip` | *(empty)* | Advanced; leave empty. Serves the REST API on one specific address instead, at the cost of the sidebar panel and the health watchdog. |
| `require_token` | `false` | Require the API token on the scanner API (`/api/v1`) too, as an ekey ESP32 device does. Recommended with `allow_external`. The integration, the pages through Home Assistant and the health watchdog keep working. Restart the add-on after changing it. |
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
