# 06: Phone setup (Termux + Termux:API)

Time: about 20 minutes. Do this on Nov 7 or the morning of Nov 8.

## 1. Install the apps (from F-Droid only)
1. On the phone, open https://f-droid.org and install the **F-Droid** app (allow installing from
   your browser when Android asks).
2. In F-Droid, install **Termux** and **Termux:API**.

**Both must come from F-Droid.** The two apps must be signed with the same key or the API
permissions do not work. If you previously installed Termux from the Play Store or GitHub, uninstall
it first.

## 2. Install packages inside Termux
Open Termux and run:
```bash
pkg update && pkg upgrade -y
pkg install -y python termux-api git
termux-setup-storage        # grant storage access (needed for photos)
```

## 3. Grant Android permissions to Termux:API
Menu names vary by brand; search Settings if you can't find them.
- **Settings → Apps → Termux:API → Permissions:** allow SMS, Phone, Call logs, Contacts, Location,
  Camera, Microphone.
- **Notification access:** Settings → Notifications (or Apps → Special app access) →
  **Notification access** / "Device & app notifications" → enable **Termux:API**.
- **Battery:** Settings → Apps → Termux → Battery → **Unrestricted** / "Don't optimise". Do the same
  for Termux:API.
- **Xiaomi / Redmi / POCO:** also enable **Autostart** for Termux, and lock Termux in Recent apps.
- **Oppo / Vivo / Realme / OnePlus:** allow background activity for Termux.

## 4. Test the commands (do this before building!)
Run each and note the output shape. Ask Claude to copy the exact shapes into
`phone_helper/mock_data/`. **Blur or replace real content before sharing anything.**
```bash
termux-battery-status
termux-wifi-connectioninfo
termux-notification-list | head -c 600
termux-sms-list -h                 # check the supported flags
termux-sms-list -l 3
termux-call-log -l 3
termux-location -p network -r once
termux-vibrate -d 300
termux-torch on; sleep 1; termux-torch off
termux-tts-speak "Hello from Phone Senses"
termux-clipboard-get
termux-volume
```
If a command hangs or prints nothing, the permission for it is missing.

To test SMS sending, send one to your own number:
```bash
termux-sms-send -n <your-own-number> "Phone Senses test"
```

## 5. Network: how the laptop reaches the phone
Option A: **Same Wi-Fi** (simplest for the demo)
- Find the phone's IP: Settings → Wi-Fi → your network → IP address (e.g. `192.168.1.23`).
- Some routers and college or office Wi-Fi block device-to-device traffic. If so, use option B.

Option B: **Tailscale** (recommended; encrypted, works anywhere)
- Install Tailscale on the phone (Play Store) and on the laptop, and log in to the same account on both.
- Use the phone's Tailscale IP (`100.x.y.z`) as `helper_url`.

Option C: **Phone hotspot**: connect the laptop to the phone's hotspot and use the phone's hotspot IP.

## 6. Run the helper (after Phase 1 is built)
```bash
cd ~
git clone https://github.com/<you>/phone-senses.git
cd phone-senses
python phone_helper/helper.py --pair                     # first time: prints the pairing code once
termux-wake-lock                                          # keep running with the screen off
python phone_helper/helper.py --host 0.0.0.0 --port 8765  # or --host <tailscale-ip>
```
Then in Hermes on the laptop set:
- `helper_url` = `http://<phone-ip>:8765`
- `helper_token` = the pairing code

Check from the laptop: `curl http://<phone-ip>:8765/v1/ping` should print `{"ok": true}`.

Optional: install **Termux:Boot** from F-Droid to start the helper automatically on reboot.

## Real-phone notes (moto g34, Android 15)
- Play Protect shows "Unsafe app blocked / built for an older version of Android" for Termux. The install still completes.
- Grant notification access to the component `com.termux.api/com.termux.api.apis.NotificationListAPI$NotificationService`.
  When granting it with adb, quote the `$`.
- Location needs background location ("Allow all the time") for Termux:API.
- If two `termux-tts-speak` calls overlap, the TTS service can jam. The helper now serialises speech.
  To recover, force-stop Termux:API.
- Calls may show an app chooser (Phone / Zoom). Pick Phone.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `termux-*` command hangs | Termux:API app missing, or installed from a different source than Termux |
| Empty notification list | Notification access not granted to Termux:API |
| `permission_denied` for SMS | Grant the SMS permission to Termux:API |
| Laptop can't reach the phone | Different networks or Wi-Fi isolation: use Tailscale or the hotspot |
| Helper stops after a few minutes | Battery optimisation: set Unrestricted, enable Autostart, run `termux-wake-lock` |
| Location times out | Use `-p network` indoors; GPS needs a sky view |
