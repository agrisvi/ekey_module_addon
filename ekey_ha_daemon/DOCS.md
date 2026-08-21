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

| Tab | On the add-on |
| --- | --- |
| Users | Full — add users, enrol a finger with live progress, adopt a fingerprint enrolled on the device itself, delete |
| Actions | LED, webhook, MQTT, KNX group write |
| Automations | Event (`match_ok` / `match_nok` / `touch`) × scope (any finger, or one) → actions |
| MQTT / KNX | Full. Settings apply immediately |
| System | Scanner identity, the serial port as a read-only row, LED brightness, clock as a status line |
| Event log | The last 100 access events, live |

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
then add it with host `localhost`, port `8080`, and the API token from step 2. Those
defaults are correct because this add-on runs with host networking on purpose.

Without the token the integration can read the scanner but cannot manage users.

## Storage

Everything persists in `/data`, which the Supervisor backs up with the add-on:

| Path | Contents |
| --- | --- |
| `/data/ekey/<device>.cfg` | The per-device pairing key. Losing it means re-pairing the scanner. |
| `/data/ekey/app/token` | The API token, `0600`. |
| `/data/ekey/app/*.json` | Users, actions, links, MQTT and KNX settings. |
| `/data/ekey/app/events.ring` | The 100-slot access log. |

A **factory reset** from the page clears the app documents, the event ring and the
current device's pairing key, then mints a new token. It does not touch other devices'
keys, and it does not touch `/data/options.json` — that is the Supervisor's, and wiping
it would take `serial_port` with it and leave an add-on that will not restart.

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| Add-on stops immediately, log says *No serial device selected* | `serial_port` is unset. Configuration tab. |
| *Failed to obtain persistent key* | Something else is talking to the same scanner. One daemon per scanner — stop the other one. |
| Sidebar page loads but the event log never updates | Only possible on a modified config: `ingress_stream` must stay `true`, or the Supervisor buffers the SSE stream. |
| `unauthorized` while installing | The container image's package visibility. It must be public; the Supervisor holds no registry credentials. |
| Integration connects but shows no users | No API token given. Re-add the integration entry with the token from the log. |
