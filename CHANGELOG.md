# Changelog

Every version of Athom Hub, newest first. Install or update from HACS, or copy the `custom_components/athom_hub` folder and restart Home Assistant.

## 0.7.2 — 2026-11-19
- Fix: smart presence sensors did not appear after a restart, and the receivers started listening in the wrong place at start-up.

## 0.7.1 — 2026-11-19
- Smart presence sensors now sit on their own device, “… smart presence”, instead of an unnamed copy of the radar.

## 0.7.0 — 2026-11-19
- **Smart presence for Athom radar sensors.** Open the sensor in Athom Hub and turn on Smart presence:
  - **Room shape and range:** draw the room's walls and set how far it looks. People behind a wall or in the next room are not counted.
  - **Named zones:** add zones like Bed, Sofa or Desk. Each one gets its own “Someone at …” sensor in Home Assistant, with its own wait before “empty”.
  - **Ignore areas:** draw around a fan, a curtain or a plant so its movement never counts.
  - **Smarter decisions:** a new person must really walk in before the room counts as taken, the motion sensor can help, and you choose how long to wait before “someone there” and before “empty”.
  - The map shows each person the sensor sees, grey with the reason when they are not counted.
- Nothing on the sensor itself is changed; its own three zones still work as before.

## 0.6.5 — 2026-11-19
- **Air conditioners follow the real remote better.** Turning the AC off with its own remote now shows Off in Home Assistant. A real remote's off also carries its temperature, so it never matched the code table exactly; Athom Hub now reads the setting bit by bit and spots the on/off bit.
- Settings the remote sends with small extras (like swing or a light on the AC) are now recognised as the closest setting instead of being ignored.

## 0.6.4 — 2026-11-16
- **Tutorials**: eight short step-by-step guides with pictures and GIFs: install, copy from a Broadlink, learn a button, use remotes in Home Assistant, air conditioners, the presence sensor, the activity list, and your dashboard.
- New README with screenshots, GIFs and one-tap "Open in HACS" and "Add integration" buttons.
- Forms for reporting a problem or suggesting an idea.

## 0.6.3 — 2026-11-16
- Athom Hub now says what kind of integration it is (remotes, air conditioning, presence), so Home Assistant and HACS can list it in the right place.

## 0.6.2 — 2026-11-16
**Ready for the HACS store**
- Athom Hub now has its own icon and logo, shown on the Integrations page and in HACS (Home Assistant 2026.3 or newer).
- The checks that Home Assistant (hassfest) and HACS run on integrations now run on GitHub for every change.
- Installing: once Athom Hub is in the HACS store you can simply search for it in HACS.

## 0.6.1 — 2026-11-16
**Air conditioner fixes**
- Changing the mode and the temperature together now sends one code, not two.
- When the Athom hears Athom Hub's own send a moment later, it no longer pulls the thermostat back to an older setting. Activity shows whether a heard AC code came from the real remote or from Athom Hub itself.

## 0.6.0 — 2026-11-16
**Easier to read on phones**
- Tabs show an icon with a one-word name, and words are never split in the middle ("Remote / s" is gone).
- The Activity filters size themselves to their word and wrap neatly on small screens.
- "From Broadlink" is now simply **Broadlink**.

## 0.5.0 — 2026-11-15
**Air conditioners: full code sets**
- Copy air conditioner code sets from SmartIR's shared library (395 Broadlink files, 110 brands), or the ones already set up in SmartIR.
- **Find my AC's code set**: press your real AC remote at the Athom and Athom Hub finds the file that has that exact code.
- An AC with a code set is a full thermostat: every mode, fan speed and temperature.
- **Follows the real remote**: when someone uses the AC's own remote near an Athom, the thermostat in Home Assistant updates by itself. Only the AC in the same room is changed.
- Fixed: thermostats keep showing the room temperature after a restart.

## 0.4.0 — 2026-11-15
- **Activity** tab: a live list of everything sent (and whether it worked) and everything heard, with the button name when it is recognised. Radio noise is left out.
- **Device controls**: every setting of an Athom device in plain words. For the presence sensor (LD2450), a live room map where you draw its zones with your finger. Restart and reset always ask first.

## 0.3.0 — 2026-11-15
- Remotes become real Home Assistant devices: air conditioner → thermostat (`climate`), curtain → `cover`, TV or audio → `media_player`, fan → `fan`, light → `light`.
- Choose what each button does ("What this button does"), and a room temperature sensor for air conditioners.

## 0.2.0 — 2026-11-15
- Picture buttons: each button gets a picture and colour from its name; both can be changed.
- A clear reaction when a button is pressed: a green tick and a short vibration, or a red shake if it did not send.

## 0.1.0 — 2026-11-15
- First version: learn infrared and 433 MHz buttons with an Athom RF/IR Remote, copy remotes from a Broadlink, a safe self-test with made-up codes, device overview, and backup and restore.
- Fixed: radio signals that the Athom reports with on and off swapped are put right.
