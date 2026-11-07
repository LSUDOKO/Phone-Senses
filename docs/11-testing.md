# 11: Testing

## Layers
1. **Unit tests** (`pytest`, no phone): parsers (OTP, money, scam), HMAC signing, input validation,
   storage, watch rules, approval hook, tool handlers with an injected fake client.
2. **Integration tests** (no phone): start `helper.py --mock` in a background thread on a random
   port; call the real `client.py` and tool handlers against it.
3. **Hermes checks:** `hermes plugins doctor . --ci` and `hermes plugins validate . --install-deps`.
4. **Manual tests on the real phone** (checklist below).

Target: `python -m pytest -q` runs in under 10 seconds.

## Synthetic SMS fixtures (all fake; extend them!)
Put these in `tests/fixtures/sms_money.json` with the expected parse result. Sender IDs, accounts,
names, refs and phone numbers are invented.

### Debits (should parse)
| # | sender | body | expected |
|---|---|---|---|
| D1 | AX-HDFCBK | `Sent Rs.250.00 From HDFC Bank A/C *4321 To ZOMATO LTD On 08/11/26 Ref 512345678901 Not You? Call 1800-000-0001/SMS BLOCK UPI to 9000000101` | debit 25000 paise, last4 4321, counterparty ZOMATO LTD, channel upi, ref 512345678901 |
| D2 | VM-SBIINB | `Dear UPI user A/C X9876 debited by 1,250.50 on date 07Nov26 trf to RAHUL KUMAR Refno 612398765432. If not u? call 1800-000-0002. -SBI` | debit 125050, last4 9876, counterparty RAHUL KUMAR |
| D3 | JD-ICICIT | `INR 99.00 spent using ICICI Bank Card XX1111 on 08-Nov-26 on NETFLIX. Avl Limit: INR 45,000.00. If not you, call 1800 000 0003/SMS BLOCK 1111 to 9000000102.` | debit 9900, last4 1111, counterparty NETFLIX, channel card |
| D4 | BZ-AXISBK | `₹500 debited from A/c no. XX2468 on 08-11-26 at 14:02 for UPI/P2M/631234567890/SWIGGY. Not you? SMS BLOCKUPI to 919000000103 - Axis Bank` | debit 50000, counterparty SWIGGY |
| D5 | AD-KOTAKB | `Rs 2000.00 withdrawn at ATM S1AW1234 from Kotak Bank a/c x5555 on 07-11-26. Avl bal Rs 10,500.00` | debit 200000, channel atm |

### Credits (should parse)
| # | sender | body | expected |
|---|---|---|---|
| C1 | AX-HDFCBK | `Money Received - INR 1,500.00 in your HDFC Bank A/c XX4321 on 08-11-26 from VPA customer123@okaxis (UPI Ref No 612300001111)` | credit 150000, counterparty customer123@okaxis |
| C2 | VM-SBIINB | `Dear SBI User, your A/c X9876-credited by Rs.25000 on 01Nov26 transfer from ACME PVT LTD Ref No 612300002222 -SBI` | credit 2500000, counterparty ACME PVT LTD |
| C3 | JD-PYTMBK | `Received Rs.80 from Anita S on 08-Nov via UPI. Ref 612300003333. -Paytm Payments Bank` | credit 8000, counterparty Anita S |

### Must be ignored (return None)
| # | sender | body | why |
|---|---|---|---|
| N1 | AX-HDFCBK | `123456 is your OTP for txn of Rs 250.00 at ZOMATO on HDFC Bank card XX1111. Valid for 5 mins. Do not share.` | OTP, not a completed transaction |
| N2 | VM-SBIINB | `Your UPI transaction of Rs 300.00 to SHOP@ybl has FAILED. Amount if debited will be reversed.` | failed |
| N3 | JD-PHONPE | `RAMESH has requested money of Rs 500 from you on PhonePe. Pay only if you know the sender.` | collect request |
| N4 | AD-BIGBZR | `FLAT 50% OFF! Shop above Rs 999 and get Rs 200 cashback. T&C. bit.ly/xyzsale` | promo |
| N5 | AX-HDFCBK | `Available balance in A/c XX4321 is Rs 12,345.67 as of 08-Nov-26.` | balance only |

## Scam fixtures (`tests/fixtures/sms_scam.json`)
| # | body | expected |
|---|---|---|
| S1 | `Dear customer your SBI account will be BLOCKED today. Update KYC immediately: http://sbi-kyc-update.co/in` | high |
| S2 | `Electricity power will be disconnected tonight at 9.30 pm because your previous month bill was not updated. Call officer 9000012345` | high |
| S3 | `Congratulations! You won Rs 25,00,000 in KBC lucky draw. Claim: bit.ly/kbcwin` | high |
| S4 | `Your parcel could not be delivered. Pay Rs 25 redelivery fee: https://indiapost-track.xyz` | high |
| S5 | `Install this app to get your refund: http://refund-help.apk.site/app.apk` | high |
| S6 | D1–D5 and C1–C3 above | low (not flagged) |

## OTP masking cases (`tests/test_otp.py`)
| input | expected |
|---|---|
| `Your OTP is 482913. Do not share.` | `Your OTP is [OTP hidden]. Do not share.` |
| `482913 is your verification code for Swiggy` | `[OTP hidden] is your verification code for Swiggy` |
| `Use code 7781 to log in` | masked |
| `Rs.1250 debited on 08/11/26` | **unchanged** (amount and date) |
| `Order #4829135 shipped` | unchanged (no OTP keyword) |
| `Call 1800 000 0003` | unchanged |

## Approval hook tests
- `phone_sms_send`, `phone_call`, `phone_photo`, `phone_otp_reveal` → returns the approve dict with
  the right `rule_key` and a message containing the full text.
- Every other tool → `None`.
- A test that fails if a new tool whose name contains `send`/`call`/`photo`/`otp` is registered
  without being in the approval list.

## Manual test checklist (real phone)
- [ ] Helper starts in Termux; `/v1/ping` reachable from the laptop
- [ ] Wrong pairing code → friendly "unauthorized" message in Hermes
- [ ] Helper stopped → friendly "phone not reachable" message
- [ ] "What's my phone battery?" correct
- [ ] "Find my phone": rings, vibrates, torch blinks; volume restored afterwards
- [ ] "Anything important on my phone?": sensible digest, no OTPs visible
- [ ] Send yourself an OTP-like SMS from another phone; it shows as `[OTP hidden]`
- [ ] "Text <your other number> hello": approval shown with full text; deny = not sent; approve = sent
- [ ] "Text Rahul" with two Rahuls in contacts: asks which one
- [ ] "Sync my bank SMS and show this week's spending": correct totals vs your bank app
- [ ] "How much did I receive today?" works
- [ ] A scam-like SMS (send one from another phone using fixture S1) is flagged
- [ ] Watch rule "tell me when a notification mentions 'delivered'" fires once, not repeatedly
- [ ] `/phone`, `/phone money week`, `/phone brief` work
- [ ] Turn on airplane mode mid-request: error is clear, Hermes keeps working
