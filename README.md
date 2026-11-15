# Athom for Dummies

A simple way to use an **Athom RF/IR Remote** (and other Athom ESP32 devices) with Home Assistant, with no coding and no re-flashing.

It adds a page called **Athom Hub** to the Home Assistant sidebar. On that page you can:

- **Learn buttons** from the remotes you already have (TV, air conditioner, fan, curtains, sockets…), one by one.
- **Copy remotes from a Broadlink** in one tap, if a Broadlink already learned them in Home Assistant.
- **Turn remotes into real devices.** An air conditioner remote becomes a thermostat (`climate`), a curtain remote becomes a curtain (`cover`), a TV remote becomes a media player, and fan and light remotes become a fan and a light. They work with the normal thermostat, curtain and media cards, in automations and with voice.
- **Press the buttons** right on the page. Big picture buttons, coloured by what they do, with a tick and a short vibration when the code was sent.
- **Control your Athom devices fully**: every setting in plain words, and for the presence sensor a live room map where you draw its zones with your finger.
- **See the activity**: a live list of everything sent and everything the Athom heard, including which of your buttons it recognised.
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

### Use your remotes in Home Assistant
Each remote becomes a device in Home Assistant:

| Remote is a… | Becomes | Works with |
|---|---|---|
| Air conditioner | `climate` | Thermostat card, `climate.set_hvac_mode`, voice |
| Curtain or blind | `cover` | Curtain or tile card, `cover.open_cover` |
| TV or audio | `media_player` | Media card, `media_player.turn_on`, volume |
| Fan | `fan` | Fan card |
| Light | `light` | Light card |

Athom Hub works out what each button does from its name ("Power", "Cool", "Open", "Vol +"…). To change it, open the remote, tap **Edit**, then **Name and picture** on a button, and choose **What this button does**.
For an air conditioner you can also pick a **room temperature sensor** in the remote's settings, so the thermostat card shows the real temperature. Temperature up and down only work if those two buttons were learned.

These devices cannot tell Home Assistant what they are doing, so their state is what Athom Hub last sent. Every button is still a normal Home Assistant `button` too, for automations.

### Presence sensor (LD2450)
Open **Devices**, tap the sensor, then **Settings and controls**:
- **Room map:** the sensor is at the top and the people it sees are dots. Choose a zone, then drag on the map to draw it, drag inside it to move it, or drag a corner to resize it. Tap **Save zone**.
- **What the zones do:** off, only see people inside the zones, or ignore people inside the zones.
- Plain switches for the rest (how long it stays "present", tracking up to 3 people, Bluetooth, status light). Restart and reset are under **Advanced** and always ask first.

### Activity
The **Activity** tab lists what was sent (and whether it worked) and what the Athom heard. Radio noise is left out; a button you saved is shown by its name when it is heard.

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
