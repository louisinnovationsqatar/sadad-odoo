# Built by Louis Innovations (www.louis-innovations.com)
import hashlib
import json
import logging
import random
import string
import base64

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# SADAD AES-128-CBC fixed IV as per SADAD spec
SADAD_AES_IV = b'@@@@&&&&####$$$$'

# Salt charset as per SADAD spec
SADAD_SALT_CHARSET = 'AbcDE123IJKLMN67QRSTUVWXYZaBCdefghijklmn123opq45rs67tuv89wxyz0FGH45OP89'

# Checkout endpoints
SADAD_CHECKOUT_URLS = {
    'v1.1': 'https://sadadqa.com/webpurchase',
    'v2.1': 'https://sadadqa.com/webpurchase',
    'v2.2': 'https://secure.sadadqa.com/webpurchasepage',
}

SADAD_API_BASE_URL = 'https://api-s.sadad.qa/api'


class PaymentProvider(models.Model):
    """Extends payment.provider to add SADAD-specific configuration fields and
    the cryptographic helpers required for SADAD checkout v1.1, v2.1 and v2.2.

    Built by Louis Innovations (www.louis-innovations.com)
    """

    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('sadad', 'SADAD')],
        ondelete={'sadad': 'set default'},
    )

    # --- Credentials ---
    sadad_merchant_id = fields.Char(
        string='Merchant ID',
        help='Your SADAD Merchant ID (7-digit number from panel.sadad.qa)',
        required_if_provider='sadad',
    )
    sadad_secret_key = fields.Char(
        string='Secret Key',
        help='Your SADAD Secret Key from the merchant panel',
        required_if_provider='sadad',
    )
    sadad_website = fields.Char(
        string='Website',
        help='The website name registered with SADAD (e.g., TESTWEBSITE)',
        required_if_provider='sadad',
    )

    # --- Checkout Settings ---
    sadad_checkout_mode = fields.Selection(
        selection=[
            ('v1.1', 'Web Checkout v1.1 — Classic redirect (SHA-256 signature)'),
            ('v2.1', 'Web Checkout v2.1 — Enhanced redirect (AES-128-CBC checksum)'),
            ('v2.2', 'Web Checkout v2.2 — Embedded payment form (AES-128-CBC checksum)'),
        ],
        string='Checkout Mode',
        default='v2.1',
        required_if_provider='sadad',
        help=(
            'v1.1: Classic redirect using SHA-256 signature. Simplest integration.\n'
            'v2.1: Enhanced redirect using AES-128-CBC encrypted checksum. More secure.\n'
            'v2.2: Embedded payment form. Customer stays on your checkout page.'
        ),
    )
    sadad_language = fields.Selection(
        selection=[
            ('eng', 'English'),
            ('arb', 'Arabic'),
        ],
        string='Checkout Language',
        default='eng',
        required_if_provider='sadad',
        help='Language displayed on the SADAD checkout page.',
    )
    sadad_order_prefix = fields.Char(
        string='Order ID Prefix',
        default='SADAD',
        help=(
            'Optional prefix prepended to Odoo order numbers when sent to SADAD. '
            'Helps avoid duplicate order ID conflicts during testing. '
            'Example: "SHOP" produces "SHOP-S00001".'
        ),
    )

    # --- Display-only information ---
    sadad_api_version = fields.Char(
        string='API Version',
        compute='_compute_sadad_api_version',
        help='The SADAD API version used by the selected checkout mode.',
    )
    sadad_callback_url = fields.Char(
        string='Callback URL',
        compute='_compute_sadad_urls',
        help='Paste this URL in your SADAD merchant panel under Callback/Return URL.',
    )
    sadad_webhook_url = fields.Char(
        string='Webhook URL',
        compute='_compute_sadad_urls',
        help='Paste this URL in your SADAD merchant panel under Webhook tab.',
    )

    # -------------------------------------------------------------------------
    # Computed fields
    # -------------------------------------------------------------------------

    @api.depends('sadad_checkout_mode')
    def _compute_sadad_api_version(self):
        for provider in self:
            mode = provider.sadad_checkout_mode or 'v2.1'
            provider.sadad_api_version = mode

    def _compute_sadad_urls(self):
        base_url = self.get_base_url()
        for provider in self:
            provider.sadad_callback_url = f'{base_url}/payment/sadad/callback'
            provider.sadad_webhook_url = f'{base_url}/payment/sadad/webhook'

    # -------------------------------------------------------------------------
    # URL helpers
    # -------------------------------------------------------------------------

    def _get_sadad_checkout_url(self):
        """Return the SADAD checkout endpoint URL for the configured mode."""
        self.ensure_one()
        mode = self.sadad_checkout_mode or 'v2.1'
        return SADAD_CHECKOUT_URLS.get(mode, SADAD_CHECKOUT_URLS['v2.1'])

    def _get_sadad_api_url(self):
        """Return the SADAD REST API base URL."""
        return SADAD_API_BASE_URL

    # -------------------------------------------------------------------------
    # Signature v1.1 — SHA-256
    # -------------------------------------------------------------------------

    def _sadad_generate_signature_v1(self, params):
        """Generate a SHA-256 signature for SADAD Web Checkout v1.1.

        Algorithm:
        1. Remove productdetail, signature, and checksumhash (case-insensitive).
        2. Sort remaining params by key (case-sensitive, ASCII order).
        3. Build string: secretKey + value1 + value2 + ... (no separators).
        4. Return sha256(string) as lowercase hex.

        :param dict params: Checkout parameters.
        :return str: 64-char lowercase hex SHA-256 hash.
        """
        self.ensure_one()
        excluded = {'productdetail', 'signature', 'checksumhash'}
        filtered = {k: v for k, v in params.items() if k.lower() not in excluded}
        sorted_params = dict(sorted(filtered.items()))
        raw = self.sadad_secret_key or ''
        for value in sorted_params.values():
            raw += str(value)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def _sadad_verify_signature_v1(self, params, checksumhash):
        """Verify a SADAD v1 callback checksum.

        :param dict params: Callback parameters (checksumhash may be included).
        :param str checksumhash: The received checksum to verify against.
        :return bool: True if valid, False otherwise.
        """
        self.ensure_one()
        clean = {k: v for k, v in params.items() if k.lower() != 'checksumhash'}
        expected = self._sadad_generate_signature_v1(clean)
        # Constant-time comparison
        return self._sadad_hmac_compare(expected, str(checksumhash))

    # -------------------------------------------------------------------------
    # Signature v2.x — AES-128-CBC
    # -------------------------------------------------------------------------

    def _sadad_generate_salt(self, length=4):
        """Generate a random salt of the given length from the SADAD charset.

        :param int length: Salt length (default 4).
        :return str: Random salt string.
        """
        return ''.join(random.choice(SADAD_SALT_CHARSET) for _ in range(length))

    def _sadad_encrypt(self, plaintext, key):
        """AES-128-CBC encrypt using SADAD's fixed IV.

        Key is truncated to 16 bytes. Output is base64-encoded.

        :param str plaintext: Text to encrypt.
        :param str key: Encryption key (will be truncated to 16 bytes).
        :return str: Base64-encoded ciphertext.
        """
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import pad
        except ImportError:
            _logger.error(
                'PyCryptodome is required for SADAD v2.x checkout. '
                'Install it with: pip install pycryptodome'
            )
            raise

        key_bytes = key.encode('utf-8')[:16]
        plaintext_bytes = plaintext.encode('utf-8')
        padded = pad(plaintext_bytes, AES.block_size)
        cipher = AES.new(key_bytes, AES.MODE_CBC, SADAD_AES_IV)
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode('utf-8')

    def _sadad_decrypt(self, ciphertext, key):
        """AES-128-CBC decrypt using SADAD's fixed IV.

        :param str ciphertext: Base64-encoded ciphertext.
        :param str key: Decryption key (will be truncated to 16 bytes).
        :return str: Decrypted plaintext.
        """
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import unpad
        except ImportError:
            _logger.error(
                'PyCryptodome is required for SADAD v2.x checkout. '
                'Install it with: pip install pycryptodome'
            )
            raise

        key_bytes = key.encode('utf-8')[:16]
        raw_data = base64.b64decode(ciphertext)
        cipher = AES.new(key_bytes, AES.MODE_CBC, SADAD_AES_IV)
        decrypted = unpad(cipher.decrypt(raw_data), AES.block_size)
        return decrypted.decode('utf-8')

    def _sadad_generate_signature_v2(self, post_data):
        """Generate an AES-128-CBC encrypted checksum for SADAD v2.x checkout.

        Algorithm:
        1. Build: {'postData': post_data, 'secretKey': secretKey}
        2. JSON-encode the dict.
        3. Generate 4-char salt from SADAD charset.
        4. Concatenate: jsonString + '|' + salt
        5. sha256(concatenated) -> 64-char hex string.
        6. Append salt: hash + salt (68 chars total).
        7. AES-128-CBC encrypt with key = (secretKey + merchantId)[:16], IV fixed.
        8. Return base64-encoded encrypted string.

        :param dict post_data: Checkout parameters.
        :return str: Base64-encoded AES encrypted checksum.
        """
        self.ensure_one()
        checksum_data = {
            'postData': post_data,
            'secretKey': self.sadad_secret_key or '',
        }
        json_string = json.dumps(checksum_data, separators=(',', ':'))
        salt = self._sadad_generate_salt(4)
        final_string = json_string + '|' + salt
        hash_hex = hashlib.sha256(final_string.encode('utf-8')).hexdigest()
        hash_string = hash_hex + salt
        key = (self.sadad_secret_key or '') + (self.sadad_merchant_id or '')
        return self._sadad_encrypt(hash_string, key)

    def _sadad_verify_webhook(self, payload, checksumhash):
        """Verify a SADAD webhook payload checksum.

        Uses the same v1 signature algorithm (SHA-256 over sorted key values).

        :param dict payload: Webhook JSON payload.
        :param str checksumhash: The checksumhash field from the payload.
        :return bool: True if valid.
        """
        self.ensure_one()
        clean = {k: v for k, v in payload.items() if k.lower() != 'checksumhash'}
        expected = self._sadad_generate_signature_v1(clean)
        return self._sadad_hmac_compare(expected, str(checksumhash))

    # -------------------------------------------------------------------------
    # Payment method codes
    # -------------------------------------------------------------------------

    def _get_default_payment_method_codes(self):
        """Include 'sadad' in the default payment method codes."""
        default_codes = super()._get_default_payment_method_codes()
        if self.code == 'sadad':
            return default_codes | {'sadad'}
        return default_codes

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    @staticmethod
    def _sadad_hmac_compare(a, b):
        """Constant-time string comparison to prevent timing attacks."""
        if len(a) != len(b):
            return False
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        return result == 0
