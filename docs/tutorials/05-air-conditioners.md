# 5 · Air conditioners: the full code set

An AC remote sends the **whole setting** (mode, fan and temperature) with every press, so learning a few buttons isn't enough. Athom Hub uses the same shared code library as SmartIR: **395 code files from 110 brands**.

## Find your AC's code set

1. Open **Athom Hub → Broadlink → Air conditioner code sets**.
2. Already use **SmartIR**? Your ACs are listed: tap **Copy**.
   Otherwise tap **Find my AC's code set**, choose the brand (or *I don't know*), and press **Power** on your real AC remote, pointed at the Athom. Athom Hub searches the library for that exact code.
3. Choose where it goes (a new remote or an AC remote you already have), which device sends it, and a room temperature sensor. Tap **Use it**.

The AC becomes a **full thermostat**: every mode, fan speed and temperature.

## It follows the real remote

Because every code is known, when someone uses the **real AC remote** near an Athom, Athom Hub recognises the setting and the thermostat in Home Assistant follows. Its own sends are recognised too and never undo what you just set.

> Tip: with [Roost Cards](https://github.com/HRadhi4/Roost-card), the **Roost Thermostat** card gives the AC a dial you drag with your finger.

**Next:** [Presence sensor →](06-presence-sensor.md)
