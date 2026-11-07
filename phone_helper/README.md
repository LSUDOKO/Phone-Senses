# Phone Senses helper (runs on your phone)

A small Python HTTP server that runs inside **Termux** on your Android phone. It wraps a fixed
set of `termux-*` commands (from Termux:API) behind an HMAC-signed JSON API. Standard library only.
No shell is used, and every endpoint runs a fixed command with validated input.

## Install (in Termux)
```bash
pkg update && pkg upgrade -y
pkg install -y python termux-api git
git clone https://github.com/LSUDOKO/Phone-Senses.git
cd Phone-Senses
python phone_helper/helper.py --pair      # prints the pairing code once
```
Paste the pairing code into the Hermes plugin setting **helper_token**.

## Run
```bash
termux-wake-lock                                          # keep running with the screen off
python phone_helper/helper.py --host 0.0.0.0 --port 8765  # or --host <your Tailscale 100.x IP>
```
Set the Hermes plugin setting **helper_url** to `http://<phone-ip>:8765`.
Check from the laptop: `curl http://<phone-ip>:8765/v1/ping` prints `{"ok": true}`.

While it runs, the helper shows an ongoing notification "Phone Senses helper running".
Stop it with Ctrl+C in Termux.

## Try it on a laptop (no phone)
```bash
python phone_helper/helper.py --pair --secret-file /tmp/ps-secret
python phone_helper/helper.py --mock --secret-file /tmp/ps-secret --port 8765
```
`--mock` serves synthetic data from `mock_data/` (fake names, +91 9000000xxx numbers).

## Options
| Flag | Default | Meaning |
|---|---|---|
| `--host` | `127.0.0.1` | Address to listen on |
| `--port` | `8765` | Port |
| `--pair` | | Create a new pairing secret (rotates the old one) and exit |
| `--mock` | | Serve fixture data instead of running Termux:API |
| `--secret-file` | `~/.phone-senses/secret` | Where the pairing secret is stored (mode 600) |

## Security
- Requests must be signed: `X-PS-Timestamp`, `X-PS-Nonce`, `X-PS-Signature`
  (HMAC-SHA256 over method, path with query, timestamp, nonce and body hash). The secret is never sent.
- Clock skew over 60 s, reused nonces and bad signatures are rejected.
- 10 requests per second overall; SMS sending and calls limited to 5 per minute.
- The log shows method, path and status only. It never logs message text or numbers.
- Use it **only on your own phone**.
