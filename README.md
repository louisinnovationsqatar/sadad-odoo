# SADAD Payment Gateway for Odoo — Free & Open Source

[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Odoo 16](https://img.shields.io/badge/Odoo-16.0-purple)](https://www.odoo.com)
[![Odoo 17](https://img.shields.io/badge/Odoo-17.0-purple)](https://www.odoo.com)
[![Odoo 18](https://img.shields.io/badge/Odoo-18.0-purple)](https://www.odoo.com)
[![Built by Louis Innovations](https://img.shields.io/badge/Built%20by-Louis%20Innovations-green)](https://www.louis-innovations.com)

**Accept payments via SADAD — Qatar's leading payment gateway. Free and open-source alternative to proprietary modules costing $199+.**

---

## Why This Module?

Proprietary SADAD modules for Odoo cost $199 per Odoo version with closed-source, obfuscated code. This module is:

- **FREE** — forever, for everyone
- **Open source** — LGPL-3, fully auditable code
- **More features** — 3 checkout modes (competitor has 2)
- **No lock-in** — fork it, customize it, use it anywhere
- **Maintained** — built by a Qatar-based Odoo consultancy

| Feature | This Module | Proprietary Alternatives |
|---------|-------------|--------------------------|
| Price | **FREE** | $199 per version |
| License | LGPL-3 (Open Source) | OPL-1 (Proprietary) |
| Source code | Fully open | Obfuscated |
| Checkout v1.1 | Yes | Yes |
| Checkout v2.1 | Yes | Yes |
| Checkout v2.2 Embedded | **Yes** | No |
| Refunds via API | Yes | Limited |
| Webhooks | Yes | Basic |
| Odoo 16/17/18 | Yes | Separate $199 purchase each |

---

## Features

- SADAD Web Checkout v1.1 (classic redirect, SHA-256 signature)
- SADAD Web Checkout v2.1 (enhanced redirect, AES-128-CBC checksum)
- SADAD Web Checkout v2.2 (embedded payment form, AES-128-CBC checksum)
- Full refund support via SADAD REST API
- Webhook notifications (server-to-server)
- Callback URL handling
- Multi-language checkout (English and Arabic)
- Order ID prefix configuration
- Transaction number logging in Odoo
- Signature verification for all callbacks and webhooks
- Integration with Odoo's standard payment status flow

---

## Requirements

- Odoo 16.0, 17.0, or 18.0
- Python package `pycryptodome` (for v2.x checkout modes)
- SADAD merchant account from [panel.sadad.qa](https://panel.sadad.qa)
- HTTPS on your Odoo instance (required for v2.2 embedded mode)

### Install PyCryptodome

```bash
pip install pycryptodome
```

---

## Installation

### Option 1: Via Odoo Apps (when published)

1. Go to Apps in Odoo
2. Search "SADAD Payment"
3. Click Install

### Option 2: Manual

```bash
# Clone into your custom addons directory
git clone https://github.com/louis-innovations/payment_sadad.git /path/to/odoo/addons/payment_sadad

# Restart Odoo and update module list
```

---

## Configuration

### 1. Open Payment Provider Settings

Go to **Invoicing → Configuration → Payment Providers → SADAD**

### 2. Enter SADAD Credentials

| Field | Source | Example |
|-------|--------|---------|
| Merchant ID | SADAD panel → Settings | `1234567` |
| Secret Key | SADAD panel → API Keys | `abc123xyz...` |
| Website | SADAD panel → Websites | `MYWEBSITE` |

### 3. Choose Checkout Mode

| Mode | Description |
|------|-------------|
| **v1.1** | Classic redirect. SHA-256 signature. Simplest. |
| **v2.1** | Enhanced redirect. AES-128-CBC checksum. Recommended. |
| **v2.2** | Embedded form. Customer stays on your page. HTTPS required. |

### 4. Copy Integration URLs

The module shows two read-only URLs that you must paste into your SADAD panel:

- **Callback URL**: `https://yoursite.com/payment/sadad/callback`
- **Webhook URL**: `https://yoursite.com/payment/sadad/webhook`

### 5. Enable the Provider

Set State to **Enabled** and save.

---

## Checkout Modes Explained

### v1.1 — Classic Redirect

Customer clicks Pay → redirected to SADAD-hosted checkout → returns via callback.

Uses SHA-256 hash over sorted parameters for signature verification.
Simple, widely tested, no additional dependencies.

### v2.1 — Enhanced Redirect

Same flow as v1.1 but uses AES-128-CBC encrypted checksum instead of plain hash.
Provides stronger tamper protection. Recommended for production.

Requires: `pycryptodome`

### v2.2 — Embedded Form

SADAD payment form loads inside an iframe on your checkout page.
Customer never leaves your website. Requires HTTPS.

Requires: `pycryptodome`

---

## Webhook Setup

1. In your SADAD merchant panel, go to **Websites → [Your Website] → Webhook**
2. Enter your webhook URL: `https://yoursite.com/payment/sadad/webhook`
3. Save

SADAD will POST JSON to this URL for every transaction event.
The module automatically processes it and updates Odoo's transaction state.

Response format (automatically returned by the module):
```json
{"status": "success"}
```

---

## Refunds

SADAD supports **full refunds only** via API.

### Limitations:
- No partial refunds (SADAD API limitation)
- Must be within **3 months** of original transaction
- Transaction must be in **Success** state

### How to Refund:
1. Go to **Invoicing → Payments**
2. Find the SADAD payment
3. Click **Refund**
4. The module calls SADAD API automatically

---

## Transaction States

| Odoo State | SADAD Status | Meaning |
|------------|-------------|---------|
| `pending` | 1 | Payment in progress |
| `done` | 3 / RESPCODE=1 | Payment successful |
| `cancel` | 2 / RESPCODE≠1 | Payment failed or cancelled |

---

## Security

The module verifies all incoming data using SADAD's checksum verification:

- **Callbacks**: SHA-256 hash verification over sorted parameters
- **Webhooks**: Same verification algorithm
- Constant-time string comparison to prevent timing attacks

---

## Developer Guide

See [doc/INTEGRATION_GUIDE.md](doc/INTEGRATION_GUIDE.md) for:

- Architecture overview
- Signature algorithm details
- How to extend the module
- API reference
- Odoo version compatibility notes

---

## Support

- **Setup Guide**: [doc/setup_guide.md](doc/setup_guide.md)
- **Bug Reports**: [GitHub Issues](https://github.com/louis-innovations/payment_sadad/issues)
- **Email**: info@louis-innovations.com
- **Website**: [www.louis-innovations.com](https://www.louis-innovations.com)

---

## Contributing

Pull requests welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

This module is maintained by **Louis Innovations** — a Qatar-based technology consultancy specialising in Odoo, eCommerce, and payment integrations.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

---

## License

LGPL-3. See [LICENSE](LICENSE).

---

## Disclaimer

SADAD, SADADQA, and related marks are trademarks of SADAD Payment Solutions.
This module is independently developed and is not affiliated with or endorsed by SADAD.

---

*Built by [Louis Innovations](https://www.louis-innovations.com) — Qatar*
