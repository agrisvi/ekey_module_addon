# Changelog

The Supervisor shows this file when an update is available, so each entry answers
one question: should I install this, and does anything change for me afterwards?

## 1.2.8

- **Option labels and help text.** The Configuration tab used to show the raw schema
  keys with no explanation. Every option now has a name and a description —
  including what `allow_external` actually exposes, which the key name does not say.
- **Fixed the health watchdog.** The probe URL used the `[PORT:8080]` placeholder,
  which the Supervisor substitutes from a `ports:` mapping — and this add-on
  deliberately has none, so there was nothing to resolve it against. It now uses the
  literal port, which `host_network: true` fixes anyway.
- Added this changelog.

No image change: 1.2.8 is 1.2.7's daemon with corrected add-on metadata.

## 1.2.7

- **New option: "Allow connections from other machines" (`allow_external`).** Ticking
  it serves the REST API on every interface. It replaces typing an address into
  `api_bind_ip` for the common case, and is not the same thing: `allow_external`
  binds `0.0.0.0`, which keeps the Supervisor bridge — and therefore the sidebar
  panel and the watchdog — working, while a single LAN address in `api_bind_ip`
  replaces that listener and breaks both.
- `api_bind_ip` still works and still takes precedence, and now warns in the log when
  its value costs you ingress.
- **`/api/v1` remains unauthenticated.** Allowing external connections puts
  fingerprint enrol/delete and the system endpoints on your network with no token in
  front of them. Firewall the port.

## 1.2.6

- Documentation for SPI RS485 HAT support.

## 1.2.5

- Sidebar entry renamed to **ekey daemon** with its own icon, so it no longer
  collides with the ekey integration's panel — both used to be called "ekey" with the
  same icon and went to different pages.

## 1.2.4

- **Dropped `armv7`.** Home Assistant is retiring 32-bit ARM and the Supervisor now
  raises a repair notice for add-ons that offer it. `aarch64` covers every Pi that
  can run HA OS. If you are somehow on a 32-bit install, this version will not appear.
- Logging goes to syslog only.

## 1.2.3

- `startup: services`, so the daemon is listening before Home Assistant Core sets up
  its config entries. Previously every boot began with the integration failing its
  first connection and retrying.
- Protocol tracing added for diagnosing scanner link problems.

## 1.2.2

- Better error handling and logging in the container entrypoint.

## 1.2.1

- Maintenance release.

## 1.2.0

- Admin page gains the actions, automations, MQTT and KNX tabs.

## 1.1.0

- The REST API and web pages from the ESP32 firmware ported to the daemon.

## 1.0.0

- First release.
