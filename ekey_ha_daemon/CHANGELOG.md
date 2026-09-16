# Changelog

The Supervisor shows this file when an update is available, so each entry answers
one question: should I install this, and does anything change for me afterwards?

## 1.2.9

- **MQTT tab restored** in the admin page. Broker settings, and the "MQTT publish"
  action type, are available again after having been temporarily hidden.
- **Serial port selection fixed** for a real USB adapter. The saved selection is now
  also matched against its `/dev/serial/by-id` alias, not just the raw device node —
  before, the "Change the serial port" dropdown could pre-select correctly on one host
  and come up completely blank on another, depending on whether udev happened to give
  that port a by-id alias (it does for essentially every USB-to-RS485 converter).
- **KNX can now go straight onto the bus, without a KNX IP Router.** The KNX tab has a
  new **Connection method**: keep *Over the network* (KNXnet/IP routing, what you have
  today) or choose *Directly attached module* for a Weinzierl KNX BAOS module wired to the
  Raspberry Pi's own UART — a kBerry 838, for instance.
  Two things are better that way. There is no router to buy or configure, and a write is
  **acknowledged**: the module confirms the bus took the telegram, so a ✓ in the event log
  finally means what it looks like it means. A routed write cannot report that at any
  price.
  One thing is different, and it is the reason this is a deliberate choice rather than
  something automatic: an attached module addresses **datapoint numbers**, not group
  addresses, because ETS owns the mapping from a datapoint to the group address it writes
  to. So actions name "datapoint 5" instead of "1/2/3", and the action editor switches
  which field it shows to match. Nothing is lost switching back and forth — both are
  stored — and existing routed setups are untouched: the default is unchanged, and a
  settings document saved before this release still means exactly what it did.
  If the module says nothing, the two usual causes are the Raspberry Pi's serial console
  still owning the UART, and a missing `dtoverlay=disable-bt` on a Pi 3/4. Both are named
  in the log rather than left to guesswork.
- **KNX can now go straight onto the bus, without a KNX IP Router.** The KNX tab has a
  new **Connection method**: keep *Over the network* (KNXnet/IP routing, what you have
  today) or choose *Directly attached module* for a Weinzierl KNX BAOS module wired to the
  Raspberry Pi's own UART — a kBerry 838, for instance.
  Two things are better that way. There is no router to buy or configure, and a write is
  **acknowledged**: the module confirms the bus took the telegram, so a ✓ in the event log
  finally means what it looks like it means. A routed write cannot report that at any
  price.
  One thing is different, and it is the reason this is a deliberate choice rather than
  something automatic: an attached module addresses **datapoint numbers**, not group
  addresses, because ETS owns the mapping from a datapoint to the group address it writes
  to. So actions name "datapoint 5" instead of "1/2/3", and the action editor switches
  which field it shows to match. Nothing is lost switching back and forth — both are
  stored — and existing routed setups are untouched: the default is unchanged, and a
  settings document saved before this release still means exactly what it did.
  If the module says nothing, the two usual causes are the Raspberry Pi's serial console
  still owning the UART, and a missing `dtoverlay=disable-bt` on a Pi 3/4. Both are named
  in the log rather than left to guesswork.
- **The pages have been restyled, and they are no longer always dark.** The access log and
  the admin panel now follow the LX/UI design system: square corners, flat cards separated
  by a hairline rather than a shadow, a deeper blue, and text fields drawn as a single
  underline instead of a full box.
  The change you will notice first is the colour. A new control in the page header — the
  half-filled circle beside *Settings* — opens a small panel with four choices.
  **Automatic** follows your device's own light/dark setting and is the new default, so on
  a machine set to light these pages will now be light. **Light** and **Dark** pin one
  regardless. If you preferred how this looked before, pick *Dark* once; the choice is
  remembered in that browser.
  The fourth, **Contrast**, is a black-and-yellow high-contrast theme for anyone who needs
  one. It is only ever chosen deliberately — nothing infers it for you.
  One limitation worth knowing: a page shown through Home Assistant's sidebar cannot read
  which theme you have set *in Home Assistant*, because ingress does not expose it. So if
  your HA theme and your device setting disagree, set the page's own theme once and it will
  stay put.

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
