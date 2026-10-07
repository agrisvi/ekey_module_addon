# Changelog

The Supervisor shows this file when an update is available, so each entry answers
one question: should I install this, and does anything change for me afterwards?

## 1.3.1

- **Live updates on the access-log and admin pages are steadier.** The pages now check
  for news every two seconds (twice a second while you enrol a finger) instead of
  keeping a stream open, so several tabs can follow the log at once, a page that was in
  the background catches up as soon as you return to it, and enrolment progress no
  longer depends on that stream staying connected. Home Assistant's own event feed is
  unchanged — nothing to do after updating.
- **Event numbers keep counting after you clear the log and restart the add-on**, instead
  of starting again at 1.

## 1.3.0

- **One version number for every ekey product, starting at 1.3.0.** The add-on, the
  Linux daemon and the ESP32 device now share a version, so the same number means the
  same code everywhere. The admin page's **System** tab has a new **Software** card
  showing the version, build date and platform. Quote these when you report a problem.
  The scanner's own firmware is now labelled **"Scanner firmware"** (it was "SW
  version"), so the two are not confused.
- **MQTT actions can now connect to a TLS broker.** Set the broker URI to
  `mqtts://<host>:8883` on the MQTT tab — for example the Mosquitto add-on's TLS port
  when it has a certificate. The broker's certificate is checked by default; tick "Skip
  TLS certificate verification" only for a trusted local broker on a self-signed
  certificate. Plain `mqtt://` brokers work exactly as before.
- **"Skip TLS certificate verification" on a webhook action now takes effect.** It was
  shown but ignored, so a webhook to a local `https://` server with a self-signed
  certificate always failed. Leave it unticked for any public or properly certified URL.
- **Hardened two edge cases that needed deliberate misuse to reach.** A webhook or MQTT
  action whose body/topic includes `{username}` (or another substitution) now safely
  encodes what gets inserted instead of copying it in raw, so a crafted name can no
  longer break a webhook's JSON body or restructure an MQTT topic. And a settings/users/
  actions/links document is now rejected if it is far more deeply nested than any real
  one needs to be, instead of being parsed regardless. Nothing changes about how you use
  the add-on, and no action is needed.
- **The access log no longer shows a deleted user as if they were still enrolled, and
  stops calling an unknown fingerprint "Granted".** Delete a user (or one of their
  fingers) and their past rows kept showing the name — right for a log, misleading about
  the device — so the **Who** column now adds **· deleted** to those rows. And a scan the
  sensor recognised but that belongs to *no* user used to show a bare fingerprint id next
  to a green **Granted**, which reads as though somebody authorised had opened the door;
  such a row now reads **· no user** and **Denied**. Both marks are explained under the
  table and on hover. Nothing about what is stored or published changes — this is how the
  page reads what was already there, so your existing 100 rows are re-read correctly too.

## 1.2.9

- **The first finger scan after a restart now reaches MQTT.** If you drive anything over
  MQTT — a Shelly relay, a light, a Home Assistant automation — the very first access
  event after the add-on started, or after you saved the MQTT tab, was silently lost: the
  add-on only opened the broker connection when it had something to send, and the send
  happened a fraction of a second before the broker had answered. The log showed
  `publish … failed: The client is not currently connected` and the door did not open;
  scanning again worked. The connection is now established at startup, so there is
  nothing to race.

  If your broker is genuinely unreachable, an action now gives up after one second rather
  than hanging the scanner — and, new in this release, **a broker that rejects your
  username or password says so in the log.** Until now that produced no message
  whatsoever, which made a typo in the MQTT tab almost impossible to find.
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
- **MQTT tab restored** in the admin page. Broker settings, and the "MQTT publish"
  action type, are available again after having been temporarily hidden.
- **Serial port selection fixed** for a real USB adapter. The saved selection is now
  also matched against its `/dev/serial/by-id` alias, not just the raw device node —
  before, the "Change the serial port" dropdown could pre-select correctly on one host
  and come up completely blank on another, depending on whether udev happened to give
  that port a by-id alias (it does for essentially every USB-to-RS485 converter).
- **An automation left with no actions can be edited again.** Deleting an action from the
  Actions tab also removes it from every automation that used it, which can leave an
  automation with none at all. Opening one of those to change its trigger or its scope then
  ran into "Select at least one action" and would not save, even though nothing about the
  action list was being changed. Editing now saves. Creating a *new* automation with no
  action is still refused, since it would do nothing at all. Such an automation is listed as
  *(no actions)* instead of an empty arrow.
- The webhook and MQTT action forms gained a "skip TLS certificate verification"
  checkbox, carried over from the shared admin page. It has **no effect on this
  add-on**: its webhook client is always verified against the system trust store, and
  its MQTT client refuses an `mqtts://` broker outright rather than connect to one
  unverified — both by design, unrelated to this checkbox.
- The **Documentation** tab's third-party software table now also names LX/UI (MIT,
  © SIA "ZZ Dats"), whose design tokens and CSS reset the pages carry. The full notice
  ships in the image as before, at `/usr/local/share/ekey/THIRD_PARTY_LICENSES`, and also
  travels inside each page itself.

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
