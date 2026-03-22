# SADAD Payment Gateway — Setup Guide

Built by Louis Innovations (www.louis-innovations.com)

---

## Prerequisites

- Odoo 16.0, 17.0, or 18.0 installation
- SADAD merchant account (register at [panel.sadad.qa](https://panel.sadad.qa))
- Your Odoo site running on HTTPS (required for v2.2 embedded mode; recommended for all modes)
- Python package `pycryptodome` installed (for v2.1 and v2.2 modes)

### Install PyCryptodome (required for v2.x checkout modes)

```bash
pip install pycryptodome
```

On Odoo.sh or Docker-based deployments, add `pycryptodome` to your `requirements.txt`.

---

## Step 1 — Install the Module

### Option A: Via Odoo Apps UI

1. Go to **Apps** in your Odoo instance.
2. Remove the "Apps" filter and search for "SADAD Payment".
3. Click **Install**.

### Option B: Manual Installation

1. Copy the `payment_sadad` folder into your Odoo addons directory (e.g., `/odoo/addons/`).
2. Restart the Odoo service.
3. In Odoo, go to **Settings → Activate developer mode**.
4. Go to **Apps → Update Apps List**.
5. Search for "SADAD Payment" and click **Install**.

---

## Step 2 — Open Payment Provider Settings

1. Go to **Invoicing** (or **Accounting**) in the top menu.
2. Navigate to **Configuration → Payment Providers**.
3. Find **SADAD** in the list and click to open it.

---

## Step 3 — Enter Your SADAD Credentials

In the **SADAD Configuration** tab:

| Field | Where to find it | Example |
|-------|-----------------|---------|
| Merchant ID | SADAD merchant panel → Settings | `1234567` |
| Secret Key | SADAD merchant panel → Settings → API Keys | `abc123xyz` |
| Website | SADAD merchant panel → Websites | `MYWEBSITE` |

**Note:** The Merchant ID must be exactly 7 digits.

### Getting Credentials from SADAD Panel

1. Log in at [panel.sadad.qa](https://panel.sadad.qa)
2. Go to **Settings** or **My Account**
3. Find your Merchant ID (7 digits)
4. Generate or view your Secret Key
5. Note your registered Website name (used in the WEBSITE parameter)

---

## Step 4 — Choose Checkout Mode

| Mode | Description | Recommended For |
|------|-------------|-----------------|
| v1.1 | Classic redirect, SHA-256 signature | Simple setups, testing |
| v2.1 | Enhanced redirect, AES-128-CBC | Most merchants (recommended) |
| v2.2 | Embedded form, AES-128-CBC | Premium UX, HTTPS required |

Set the **Checkout Mode** dropdown to your preferred option.

Set **Checkout Language** to English or Arabic based on your customers.

---

## Step 5 — Configure Callback and Webhook URLs

After entering your credentials, two URLs will appear in the **Integration URLs** section:

- **Callback URL**: `https://yoursite.com/payment/sadad/callback`
- **Webhook URL**: `https://yoursite.com/payment/sadad/webhook`

### Setting Up in SADAD Panel

1. Log in to [panel.sadad.qa](https://panel.sadad.qa)
2. Go to **Websites** → select your website
3. Find **Return URL** or **Callback URL** field
4. Paste the **Callback URL** from Odoo
5. Find the **Webhook** tab or **Webhook URL** field
6. Paste the **Webhook URL** from Odoo
7. Save changes

**Important:** Both URLs must be publicly accessible (not localhost).

---

## Step 6 — Optional: Set Order ID Prefix

In the **Advanced** section, you can set an Order ID Prefix such as `SHOP`.

This produces order IDs like `SHOP-S00001` sent to SADAD, which helps avoid conflicts during testing.

---

## Step 7 — Enable the Provider

1. In the provider form, set **State** to **Enabled** (or use the toggle).
2. To show on eCommerce, also toggle **Published on Website** if needed.
3. Click **Save**.

---

## Step 8 — Test with SADAD Test Credentials

SADAD provides test credentials for sandbox testing:

1. Get test credentials from SADAD (contact SADAD support or use their sandbox portal).
2. Enter the test Merchant ID and Secret Key.
3. Place a test order on your Odoo shop.
4. Select SADAD at checkout.
5. Use SADAD test card details on the payment page.
6. Verify the payment appears as "Done" in Odoo.
7. Check the Webhook URL receives a notification.

---

## Step 9 — Go Live

1. Replace test credentials with live credentials in the provider settings.
2. Ensure the website is on HTTPS.
3. Confirm Callback and Webhook URLs are correct in the SADAD panel.
4. Process a real test transaction with a small amount.
5. Verify refund functionality works.

---

## Troubleshooting

### Payment fails with "Invalid signature"
- Double-check your Secret Key (no extra spaces, exact value from SADAD panel).
- Ensure your server time is accurate (time skew can affect signatures).

### Callback not received
- Ensure the Callback URL is publicly accessible (not localhost or behind a firewall).
- Check Odoo server logs for incoming POST requests to `/payment/sadad/callback`.

### Webhook not working
- Verify the Webhook URL is set in the SADAD merchant panel.
- Check that your server returns HTTP 200 with `{"status": "success"}`.
- Review Odoo logs for webhook processing errors.

### "PyCryptodome not found" error
- Required for v2.1 and v2.2 modes.
- Install with: `pip install pycryptodome`
- Add to requirements.txt if using Docker/Odoo.sh.

### Orders stuck in "Pending" state
- SADAD may not have sent the webhook yet (can take a few minutes).
- Check your SADAD webhook configuration in the panel.
- You can manually check transaction status in the SADAD panel and update the order.

---

## Refund Process

1. Go to **Invoicing → Payments** and find the SADAD payment.
2. Click **Refund**.
3. The module will call the SADAD API to issue a full refund.

**Refund limitations:**
- Full refunds only (SADAD does not support partial refunds via API)
- Must be within 3 months of original transaction
- Transaction must be in "Success" state

---

## Support

- **GitHub Issues**: Report bugs and request features via GitHub
- **Email**: info@louis-innovations.com
- **Website**: https://www.louis-innovations.com

---

*Built by Louis Innovations (www.louis-innovations.com) — Free & Open Source*
