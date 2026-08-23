# ekey module Daemon

The RS485 backend for the **ekey module fingerprint scanner** (OEM version). It owns the
users, their fingerprints, the automations and the access log, and serves them over an
HTTP/SSE API plus its own management pages.

## First run

1. **Configuration** tab → `serial_port` → pick your RS485 converter → **Save**.
   Required. The add-on exits with *"No serial device selected"* without it, on purpose:
   the fix belongs in this tab, not in a page the add-on serves.
2. **Start**, then open the **Log** tab. Two lines matter:
   - `App API token (for the Home Assistant integration): …` — copy it, the integration
     needs it. It is printed only when first minted; afterwards read it from
     `/data/ekey/app/token`.
   - `app_pages: serving 3 page(s)` — confirms the sidebar panel will work.
3. Click **ekey** in the sidebar. No token needed there: Home Assistant has already
   authenticated you and the Supervisor proxies the request.

## Options

| Option | Default | What it does |
| --- | --- | --- |
| `serial_port` | *(empty)* | The RS485 device, from a dropdown of what is currently attached. Internal (non-USB) ports appear too. To change it: reselect → **Save** → **Restart** (the device is read at startup). |
| `api_bind_ip` | *(empty)* | Also serve the REST API on this address. Empty means loopback plus the Supervisor's bridge only. **`/api/v1` is unauthenticated** — set this only on a trusted network, and only deliberately. |
| `log_request_bodies` | `false` | Write request bodies to the log. They carry user names and fingerprint template hex, and add-on logs are copied into support bundles. Turn it on while debugging, then off. |

## What the sidebar page can do here

**ekey** in the sidebar opens the **access log** — the last 100 access and action
events, live. That is the landing page, not a tab. **Settings** in its header opens the
admin page, and the tabs are there:

| Tab | On the add-on |
| --- | --- |
| Users | Full — add users, enrol a finger with live progress, adopt a fingerprint enrolled on the device itself, delete |
| Actions | LED, webhook, MQTT, KNX group write |
| Automations | Event (`match_ok` / `match_nok` / `touch`) × scope (any finger, or one) → actions |
| MQTT / KNX | Full. Settings apply immediately |
| System | Scanner identity, the serial port as a read-only row, LED brightness, a read-only clock, **Generate new API token**, and a control to clear the event ring |

The page asks the daemon what it can do (`GET /app/v1/capabilities`) and hides the rest,
so what you see is what this backend can actually run — no tab is offered that would
fail when used.

**Automations run here, not in Home Assistant.** That is the reason they live on the
backend: a recognised finger still fires its actions while Home Assistant is restarting,
updating or broken.

Three things the page deliberately does *not* offer in this deployment, because something
else already owns each job:

- **No serial-port picker** — the Supervisor owns the device assignment.
- **No device-name / certificate card** — ingress already terminates TLS, and the
  container has no avahi to publish a name with.
- **No `gpio` action type** — the host's GPIO lines are not a container's to claim. To
  drive a relay, write a Home Assistant automation on the `ekey_access_granted` event, or
  use the `toggle_relay_on_granted` blueprint that ships with the integration.

The daemon is started with `--no-serial-select --no-gpio`, so which product this is can
be read off the process line rather than inferred from the environment.

## The Home Assistant integration

Install **[ekey module App](https://github.com/agrisvi/ekey_module_app)** through HACS,
then **Settings → Devices & Services → Add Integration** and search for
**ekey module App**.

It asks first how Home Assistant reaches the backend. Choose
**Local — ekey-ha-daemon on this host (HTTP)**, and take the defaults: host
`127.0.0.1`, port `8080`. Those are correct because this add-on runs with host
networking on purpose. Then paste the API token from step 2.

Without the token the integration can read the scanner but cannot manage users — the
panel needs it.

If you later use **Generate new API token** on the System tab, the old one stops
working immediately and the integration raises a *"ekey token no longer accepted"*
notice. Entering the new token there is the whole fix; the integration does not need
to be removed and re-added.

## Storage

Everything persists in `/data`, which the Supervisor backs up with the add-on. The
daemon itself writes to `/etc/ekey`; the container symlinks that whole directory to
`/data/ekey` at startup, so both paths name the same files and either one works if you
go looking from a shell.

| Path | Contents |
| --- | --- |
| `/data/ekey/<device>.cfg` | The per-device pairing key. Losing it means re-pairing the scanner. |
| `/data/ekey/app/token` | The API token, `0600`. |
| `/data/ekey/app/*.json` | Users, actions, links, MQTT and KNX settings. |
| `/data/ekey/app/events.ring` | The 100-slot log of access and action events, oldest overwritten first. |

There is **no factory reset** on this backend — the page reports
`factory_reset: false` and offers no such control. To start clean, use the individual
controls instead: **Clear log…** on the System tab empties the event ring, users and
fingerprints are deleted from the Users tab, and **Generate new API token** replaces
the token.

`/data/options.json` is the Supervisor's, not the daemon's. Nothing here writes to it,
which is deliberate: wiping it would take `serial_port` with it and leave an add-on
that will not restart.

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| Add-on stops immediately, log says *No serial device selected* | `serial_port` is unset. Configuration tab. |
| *Failed to obtain persistent key* | Something else is talking to the same scanner. One daemon per scanner — stop the other one. |
| Sidebar page loads but the event log never updates | Only possible on a modified config: `ingress_stream` must stay `true`, or the Supervisor buffers the SSE stream. |
| `unauthorized` while installing | The container image's package visibility. It must be public; the Supervisor holds no registry credentials. |
| Integration connects but shows no users | No API token given. Re-add the integration entry with the token from the log. |

## Third-party software

This add-on's container image contains software from the projects below in addition to
the daemon itself. All of them are unmodified builds installed from the Debian archive
and linked dynamically, with one exception noted in the table.

| Component | Used under | Notes |
| --- | --- | --- |
| [cJSON](https://github.com/DaveGamble/cJSON) 1.7.19 | MIT | **The exception**: compiled directly into the daemon and the scanner library, not installed as a package. Unmodified upstream source. |
| [GNU libmicrohttpd](https://www.gnu.org/software/libmicrohttpd/) | LGPL-2.1-or-later | The HTTP and SSE server. Dynamically linked, so you may replace it with your own build by substituting the shared library in the image — no relinking needed. |
| [Mbed TLS](https://github.com/Mbed-TLS/mbedtls) | **Apache-2.0** | ECDH and AES-GCM on the scanner link, and the self-signed HTTPS certificate. Upstream offers Apache-2.0 **or** GPL-2.0-or-later; this distribution takes Apache-2.0, so no GPL obligation attaches on its account. |
| [libcurl](https://curl.se/) | curl licence (MIT/X style) | The `webhook` action type. |
| [Eclipse Mosquitto](https://github.com/eclipse-mosquitto/mosquitto) | **BSD-3-Clause** | The `mqtt` action type. Upstream offers EPL-2.0 **or** BSD-3-Clause; this distribution takes BSD-3-Clause, so the EPL's source-availability provisions do not apply. |
| Home Assistant Debian base image | assorted | Debian Bookworm userland; each package carries its own copyright file. |

Where the licence choice is shown in bold, that choice is part of the notice — a reader
should not have to work out which of two sets of obligations applies.

### Reading the full texts

Everything is inside the image. From a terminal on the Home Assistant host:

```bash
docker exec addon_<slug>_ekey_ha_daemon cat /usr/local/share/ekey/THIRD_PARTY_LICENSES
docker exec addon_<slug>_ekey_ha_daemon ls  /usr/local/share/ekey/licenses/
```

`THIRD_PARTY_LICENSES` is the notice itself. The `licenses/` directory holds one file per
package, copied verbatim from that package's own Debian copyright file at image build
time, plus `installed-versions.txt` recording the exact version each notice belongs to —
a licence naming no version is guesswork the moment Debian ships a new one.

The daemon itself is not covered by any of the above. Its open components are MIT; the
scanner driver (`libekey_scanner.so`) is proprietary and not published in source form.

If something ships in the image and is not named here, that is a defect in this list
rather than a licence you have to guess at — please
[open an issue](https://github.com/agrisvi/ekey_module_addon/issues).
