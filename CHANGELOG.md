# Changelog

All notable changes to the SADAD Payment Gateway for Odoo module are documented here.

Format: [Semantic Versioning](https://semver.org/)
Built by Louis Innovations (www.louis-innovations.com)

---

## [1.0.0] — 2024-03-22

### Added
- Initial release of SADAD Payment Gateway for Odoo
- Web Checkout v1.1 support (SHA-256 signature)
- Web Checkout v2.1 support (AES-128-CBC checksum)
- Web Checkout v2.2 embedded form support (AES-128-CBC checksum)
- Callback URL handler at `/payment/sadad/callback`
- Webhook handler at `/payment/sadad/webhook`
- Full refund support via SADAD REST API
- Multi-language checkout (English and Arabic)
- Order ID prefix configuration
- SADAD transaction number storage on payment.transaction
- Signature verification for callbacks and webhooks
- Admin form view with credentials, checkout settings, and integration URLs
- Arabic translations (i18n/ar.po)
- Odoo 16.0, 17.0, and 18.0 compatibility
- Setup guide and integration developer guide
- MIT-friendly LGPL-3 license

---

## [Unreleased]

### Planned
- Odoo 18.0 explicit testing and certification
- Automated test suite with mock SADAD responses
- Multi-company support improvements
- QR code payment option (if SADAD adds support)

---

*Built by Louis Innovations (www.louis-innovations.com)*
