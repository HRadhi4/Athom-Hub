# Athom for Dummies

A simple way to use an **Athom RF/IR Remote** (and other Athom ESP32 devices) with Home Assistant, with no coding and no re-flashing.

It adds a page called **Athom Hub** to the Home Assistant sidebar. On that page you can:

- **Learn buttons** from the remotes you already have (TV, air conditioner, fan, curtains, sockets…), one by one.
- **Copy remotes from a Broadlink** in one tap, if a Broadlink already learned them in Home Assistant.
- **Press the buttons** right on the page. Every button is also a normal Home Assistant button, so it works on dashboards, in automations and with voice.
- **Check that it works** with a safe test that sends a made-up code. Your TV, AC and curtains will not react.
- **See your Athom devices** (remote, presence sensor…): online or offline, room, Wi-Fi signal and a few live readings. Tap a device to see more.
- **Save a backup** of all your remotes to a file, and bring it back later.

Everything stays on your own Home Assistant. Nothing is sent to the internet.

---

## What you need

- Home Assistant **2026.11 or newer**.
- An **Athom RF/IR Remote** already added to Home Assistant. It shows up by itself under *Settings → Devices & services → ESPHome*. Keep the factory software that came on it. You do **not** need to re-flash it.
- Optional: a Broadlink (RM4 Pro, RM4 mini…) whose remotes you want to copy.

## Install

### With HACS (easiest)
1. Open **HACS** → the three dots at the top right → **Custom repositories**.
2. Paste this repository's address, choose **Integration**, and tap **Add**.
3. Find **Athom Hub** in HACS, tap **Download**.
4. **Restart** Home Assistant (*Settings → System → Restart*).

### By hand
1. Download this repository (green **Code** button → **Download ZIP**).
2. Copy the folder `custom_components/athom_hub` into your Home Assistant `config/custom_components/` folder (with the *File editor*, *Samba* or *Studio Code Server* add-on).
3. **Restart** Home Assistant.

### Then
1. Go to *Settings → Devices & services → Add integration*, search **Athom Hub**, tap it. There is nothing to fill in.
2. **Athom Hub** now appears in the sidebar (only for administrators).

---

## How to use it

### Copy your Broadlink remotes
1. Open **Athom Hub → From Broadlink**.
2. Tap a remote to see its buttons, then tap **Copy to Athom Hub**.
3. Open the new remote and press each button once to check that the real device reacts.

The Broadlink keeps working. Nothing is removed from it.

### Learn a new button
1. **Remotes → New remote**. Give it a name and choose what it controls.
2. Tap **Add a button**, then choose **Infrared** (you point it: TV, AC, fan, audio) or **Radio 433 MHz** (works through walls: curtains, sockets).
3. When it says *Press the button now*:
   - **Infrared:** point the remote at the Athom from about 30 cm and press once.
   - **Radio:** hold the remote close to the Athom and keep the button pressed for about two seconds.
4. Tap **Try it**. If the device reacted, give the button a name and **Save**.

### Check that it works
**Devices → Check that it works** sends a made-up code from the Athom (or from a Broadlink) and listens for it with the Athom's receiver. A green line means sending and hearing both work.

### Use the buttons elsewhere
Each remote becomes a device in Home Assistant with one button per remote button (for example `button.living_room_tv_power`). Put them on a dashboard or call `button.press` in an automation.

---

## Air conditioners

The Athom RF/IR Remote also has a built-in **air conditioner** control (a *climate* entity), which speaks one AC brand's "language". Out of the box it is set to **Coolix**, used by Midea and the many AC brands Midea builds for.

**How to find out if your AC speaks Coolix:**
1. Open Athom Hub → **Add a button** → **Infrared**, and press your AC remote's power button.
2. In *Settings → Devices & services → ESPHome → Athom RF/IR Remote*, open the AC control, turn it on and set a temperature.
3. If your AC beeps and follows, you are done: use that climate entity.

If it does not react, your AC speaks another language. Learn the buttons you need (power, cool, temperature up and down) as normal buttons instead.

---

## Good to know

- **Remotes learned only in the Broadlink phone app** are not in Home Assistant, so they cannot be copied. Learn those buttons again with Athom Hub.
- **Rolling-code remotes** (garage doors, some gates and shutters) change their code every press. No device can copy them.
- **Radio replay through the Athom** works for simple 433 MHz remotes (curtains, sockets, doorbells). Test each button once after copying.
- The Athom's radio receiver hears background radio noise all the time. That is normal; Athom Hub only keeps a radio code after hearing the same signal at least three times.
- Codes are kept in Home Assistant's own storage and are included in Home Assistant backups.

## Problems?

| What you see | What to do |
|---|---|
| *No remote sender found* | Add the Athom RF/IR Remote to Home Assistant first (ESPHome). |
| *… is offline* | Check that the Athom has power and Wi-Fi. |
| *Nothing clear was heard* | Come closer, point straight at the Athom, avoid bright sunlight. For radio, hold the button longer. |
| The button sends but the device does not react | Learn it again, standing closer. For an AC, learn it with the AC already off. |

## For developers

The code-conversion maths (`custom_components/athom_hub/codes.py`) has no Home Assistant imports and is tested on its own:

```
python -m pytest tests
```

Athom Hub sends and listens through Home Assistant's `infrared` and `radio_frequency` entity platforms, so any emitter or receiver that Home Assistant offers there can be used, not only Athom devices.

## License

GPL-3.0. See [LICENSE](LICENSE).
