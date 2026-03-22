# SADAD Payment Gateway — Developer Integration Guide

Built by Louis Innovations (www.louis-innovations.com)

---

## Architecture Overview

The module follows Odoo's standard payment provider architecture:

```
payment_sadad/
├── models/
│   ├── payment_provider.py      # Provider configuration + crypto helpers
│   └── payment_transaction.py  # Transaction lifecycle + form data
├── controllers/
│   └── main.py                  # HTTP endpoints (callback, webhook)
├── views/
│   ├── payment_provider_views.xml   # Admin form view
│   └── payment_sadad_templates.xml  # Checkout QWeb templates
└── static/
    └── src/
        ├── js/payment_form.js   # Frontend JS (auto-submit, iframe)
        └── css/payment_sadad.css
```

### Flow: Customer Checkout

```
Customer clicks "Pay" (Odoo checkout)
    → Odoo calls payment_transaction._get_specific_rendering_values()
    → Module builds SADAD POST params + signature/checksum
    → QWeb template renders hidden form
    → JS auto-submits form to SADAD endpoint
    → Customer interacts with SADAD payment page
    → SADAD POSTs callback to /payment/sadad/callback
    → SadadController.sadad_callback() processes it
    → _handle_notification_data() → _process_notification_data()
    → Transaction state updated (done/cancelled/pending)
    → Customer redirected to /payment/status
    → SADAD also POSTs webhook to /payment/sadad/webhook (async)
```

---

## Signature Algorithms

### v1.1 — SHA-256 Signature

Located in: `payment_provider.py → _sadad_generate_signature_v1()`

```python
# 1. Filter out excluded keys (productdetail, signature, checksumhash)
# 2. Sort by key (case-sensitive, ASCII/SORT_STRING order)
# 3. Build: secretKey + value1 + value2 + ...
# 4. SHA-256 hex hash
```

**Key insight:** Python's `dict(sorted(params.items()))` with no `key=` uses
lexicographic (ASCII) ordering, which matches PHP's `ksort($arr, SORT_STRING)`.
Uppercase letters come before lowercase in ASCII order.

### v2.x — AES-128-CBC Checksum

Located in: `payment_provider.py → _sadad_generate_signature_v2()`

```python
# 1. Build: {'postData': params, 'secretKey': secretKey}
# 2. json.dumps(data, separators=(',', ':'))  # compact JSON, no spaces
# 3. salt = random 4 chars from SADAD_SALT_CHARSET
# 4. final = jsonString + '|' + salt
# 5. hash_hex = sha256(final.encode('utf-8')).hexdigest()  # 64 chars
# 6. hash_string = hash_hex + salt  # 68 chars
# 7. key = (secretKey + merchantId)[:16]
# 8. AES-128-CBC encrypt(hash_string, key, iv=b'@@@@&&&&####$$$$')
# 9. base64_encode(ciphertext)
```

**Critical details:**
- JSON must be compact (no spaces after `:` or `,`)
- IV is always `@@@@&&&&####$$$$` (fixed 16 bytes)
- Key is `(secretKey + merchantId)` truncated to exactly 16 bytes
- PyCryptodome handles PKCS#7 padding automatically via `Crypto.Util.Padding.pad`

---

## Adding Custom Fields to Checkout

To add extra data to the SADAD checkout POST, override
`_get_specific_rendering_values` in a new module:

```python
from odoo import models

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'sadad':
            return res

        # Add custom fields
        res['CUSTOM_FIELD'] = 'custom_value'

        # Note: if adding fields that should be included in v1.1 signature,
        # you must regenerate the signature AFTER adding them.
        # The signature excludes: productdetail, signature, checksumhash.

        return res
```

---

## Adding Custom Provider Configuration Fields

Extend `payment.provider` in your own module:

```python
from odoo import fields, models

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    my_sadad_custom_field = fields.Char(
        string='Custom Setting',
        help='My custom SADAD setting',
    )
```

Then extend the view `payment_sadad.payment_provider_sadad_form_view`
using XPath to add your field to the SADAD Configuration tab.

---

## Webhook Verification

The webhook controller at `/payment/sadad/webhook` receives JSON:

```json
{
    "invoiceNumber": "SADAD-S00001",
    "isTestMode": false,
    "merchantId": "1234567",
    "message": "Transaction Successful",
    "transactionNumber": "TXN123456",
    "transactionStatus": 3,
    "txnAmount": "100.00",
    "websiteRefNo": "SADAD-S00001",
    "checksumhash": "base64encodedchecksumhere"
}
```

`transactionStatus` values:
- `1` = In Progress
- `2` = Failed
- `3` = Success (triggers `_set_done()`)

The webhook must return HTTP 200 with `{"status": "success"}`.

---

## Callback POST Parameters

The callback at `/payment/sadad/callback` receives POST form data:

| Parameter | Description |
|-----------|-------------|
| `website_ref_no` | Merchant's order ID |
| `transaction_status` | 1=progress, 2=failed, 3=success |
| `transaction_number` | SADAD transaction number |
| `MID` | Merchant ID |
| `RESPCODE` | 1 = success |
| `RESPMSG` | Human-readable response message |
| `ORDERID` | Order ID (same as ORDER_ID sent) |
| `STATUS` | `TXN_SUCCESS` or `TXN_FAILED` |
| `TXNAMOUNT` | Transaction amount |
| `checksumhash` | Signature for verification |

---

## Refund API

The refund flow uses SADAD's REST API:

### Step 1: Authenticate

```
POST https://api-s.sadad.qa/api/userbusinesses/login
Content-Type: application/json

{
    "sadadId": 1234567,
    "secretKey": "your-secret-key",
    "domain": "YOURWEBSITE"
}

Response:
{
    "accessToken": "eyJ..."
}
```

### Step 2: Submit Refund

```
POST https://api-s.sadad.qa/api/transactions/refundTransaction
Authorization: Bearer eyJ...
Content-Type: application/json

{
    "transactionnumber": "TXN123456"
}
```

**Limitations:**
- Full refunds only (no `amount` parameter accepted by SADAD)
- Transaction must be in Success state (status 3)
- Must be within 90 days of transaction date

---

## Transaction Status Check

To check a transaction status manually:

```
GET https://api-s.sadad.qa/api/transactions/getTransaction?transactionnumber=TXN123456
Authorization: Bearer eyJ...
```

---

## Odoo Payment Provider API Reference (v17)

Key methods used from Odoo's base `payment.provider` model:

| Method | Purpose |
|--------|---------|
| `get_base_url()` | Returns the public base URL of the Odoo instance |
| `_get_default_payment_method_codes()` | Override to add 'sadad' code |

Key methods used from Odoo's base `payment.transaction` model:

| Method | Purpose |
|--------|---------|
| `_get_specific_rendering_values(processing_values)` | Build provider-specific form data |
| `_get_tx_from_notification_data(provider_code, data)` | Find TX from callback data |
| `_process_notification_data(data)` | Update TX state from notification |
| `_handle_notification_data(provider_code, data)` | Orchestrates find + process |
| `_set_done()` | Mark transaction as successful |
| `_set_pending()` | Mark transaction as pending |
| `_set_canceled(state_message)` | Mark transaction as cancelled |
| `_set_error(state_message)` | Mark transaction as error |
| `_send_refund_request(amount_to_refund)` | Override for refund flow |

---

## Testing Without SADAD Credentials

For unit testing the signature algorithms:

```python
from odoo.addons.payment_sadad.models.payment_provider import PaymentProvider

# v1.1 signature test
params = {
    'merchant_id': '1234567',
    'ORDER_ID': 'TEST-001',
    'TXN_AMOUNT': '100.00',
}
# Create a mock provider record and call _sadad_generate_signature_v1(params)
```

The PHP SDK test suite at `/c/projects/sadad-php-sdk/tests/` contains
reference test vectors that can be used to verify Python implementation parity.

---

## Odoo Version Compatibility Notes

### Odoo 17.0 (Primary)
Full support. All APIs used are stable in 17.0.

### Odoo 16.0
Compatible. The `payment.provider` / `payment.transaction` model names
and key methods are the same. Minor differences in view inheritance may
require adjustments.

### Odoo 18.0
Should be compatible. Monitor for changes to:
- `payment.provider` field names
- `payment.transaction._handle_notification_data()` signature
- Frontend asset loading (`web.assets_frontend`)

---

## Contributing

See `CONTRIBUTING.md` in the repository root for contribution guidelines.

Bugs: GitHub Issues or info@louis-innovations.com

---

*Built by Louis Innovations (www.louis-innovations.com)*
