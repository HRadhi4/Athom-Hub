# 2 · Bring in your Broadlink codes

**Time: 1 minute per remote.** If a Broadlink already learned your remotes, bring their codes into Athom Hub instead of learning every button again.

1. Open **Athom Hub → Broadlink**.
2. Paste the codes, one button per line, for example:
   ```
   power: JgBQAAABKZQTEhMSExITEhMS...
   volume up: JgBQAAABKZQTEhMSExITEh...
   ```
   Codes starting with `b64:` work too. Or tap **Choose a file** and pick a saved file of codes (a text file, or a JSON file of `{"button": "code"}` or `{"remote": {"button": "code"}}`).
3. Tap **Read the codes**, open the remote, then tap **Copy to Athom Hub**. The new remote opens.
4. Press each button once and check that the real device reacts.

The Broadlink keeps working. Nothing is removed from it, and Athom Hub only reads what you paste or choose.

> **Where do I find the codes?** Anywhere you kept them: notes, a codes file you saved, or a code shared for your device model. Codes that exist only inside the Broadlink phone app can't be exported: [learn those buttons](03-learn-a-button.md) instead. **Rolling-code** remotes (garage doors, some gates) change their code every press; no device can copy them.

**Next:** [Learn a button →](03-learn-a-button.md)
