# Built by Louis Innovations (www.louis-innovations.com)
import json
import logging
from datetime import datetime

import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Extends payment.transaction to handle SADAD-specific payment flows.

    Implements checkout form data building, callback/webhook processing,
    and refund via the SADAD REST API.

    Built by Louis Innovations (www.louis-innovations.com)
    """

    _inherit = 'payment.transaction'

    sadad_transaction_number = fields.Char(
        string='SADAD Transaction Number',
        readonly=True,
        help='Transaction number assigned by SADAD after successful payment.',
    )
    sadad_order_id = fields.Char(
        string='SADAD Order ID',
        readonly=True,
        help='The ORDER_ID value sent to SADAD (with prefix applied).',
    )
    sadad_response_code = fields.Char(
        string='SADAD Response Code',
        readonly=True,
        help='RESPCODE returned in the callback (1 = success).',
    )
    sadad_response_message = fields.Char(
        string='SADAD Response Message',
        readonly=True,
        help='RESPMSG returned in the callback.',
    )

    # -------------------------------------------------------------------------
    # Rendering values — build the SADAD form POST data
    # -------------------------------------------------------------------------

    def _get_specific_rendering_values(self, processing_values):
        """Build the SADAD checkout form data for the payment form template.

        Called by Odoo's payment module when rendering the payment page.
        Returns a dict that is passed to the QWeb template as rendering values.

        :param dict processing_values: Payment processing values from Odoo core.
        :return dict: Rendering values including api_url and all SADAD POST params.
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'sadad':
            return res

        provider = self.provider_id
        base_url = provider.get_base_url()

        # Build the prefixed order ID
        prefix = (provider.sadad_order_prefix or '').strip()
        order_id = f'{prefix}-{self.reference}' if prefix else self.reference

        # Store for later lookup
        self.sadad_order_id = order_id

        # Customer info
        partner = self.partner_id
        mobile = ''.join(filter(str.isdigit, partner.phone or partner.mobile or ''))
        email = partner.email or ''

        # Build core checkout params
        params = {
            'merchant_id': provider.sadad_merchant_id or '',
            'ORDER_ID': order_id,
            'WEBSITE': provider.sadad_website or '',
            'TXN_AMOUNT': f'{self.amount:.2f}',
            'CALLBACK_URL': f'{base_url}/payment/sadad/callback',
            'MOBILE_NO': mobile,
            'EMAIL': email,
            'txnDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'SADAD_WEBCHECKOUT_PAGE_LANGUAGE': (provider.sadad_language or 'eng').upper(),
        }

        # Build product detail from sale order lines if available
        product_detail = self._build_sadad_product_detail()

        # Multi-product flag
        if len(product_detail) > 1:
            params['VERSION'] = '1.1'

        mode = provider.sadad_checkout_mode or 'v2.1'

        if mode == 'v1.1':
            params['signature'] = provider._sadad_generate_signature_v1(params)
        else:
            # v2.1 and v2.2 use AES-128-CBC checksum
            params['checksumhash'] = provider._sadad_generate_signature_v2(params)

        # Add product detail after signature (excluded from signature per spec)
        if product_detail:
            # Serialised as JSON string for POST form
            params['productdetail'] = json.dumps(product_detail)

        return {
            'api_url': provider._get_sadad_checkout_url(),
            'is_embedded': mode == 'v2.2',
            **params,
        }

    def _build_sadad_product_detail(self):
        """Build SADAD productdetail array from linked sale order lines.

        Falls back to a single-item list using the transaction amount
        and reference if no sale order is linked.

        :return list: List of product detail dicts.
        """
        self.ensure_one()
        # Try to get sale order from the source document
        sale_order = None
        if hasattr(self, 'sale_order_ids') and self.sale_order_ids:
            sale_order = self.sale_order_ids[0]
        elif hasattr(self, 'invoice_ids') and self.invoice_ids:
            # Invoice-based payment — use invoice lines
            invoice = self.invoice_ids[0]
            items = []
            for line in invoice.invoice_line_ids:
                if line.display_type == 'product':
                    items.append({
                        'order_id': str(line.id),
                        'amount': f'{line.price_total:.2f}',
                        'quantity': str(int(line.quantity)),
                    })
            if items:
                return items

        if sale_order:
            items = []
            for line in sale_order.order_line:
                if not line.is_delivery and line.product_id:
                    items.append({
                        'order_id': str(line.id),
                        'amount': f'{line.price_total:.2f}',
                        'quantity': str(int(line.product_uom_qty)),
                    })
            if items:
                return items

        # Fallback: single product representing full transaction
        return [{
            'order_id': self.reference,
            'amount': f'{self.amount:.2f}',
            'quantity': '1',
        }]

    # -------------------------------------------------------------------------
    # Notification data — find transaction from callback/webhook
    # -------------------------------------------------------------------------

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Find the payment.transaction record matching incoming SADAD data.

        Supports both callback POST params (ORDERID key) and webhook JSON
        payloads (websiteRefNo / invoiceNumber keys).

        :param str provider_code: Must be 'sadad'.
        :param dict notification_data: Callback POST params or webhook JSON.
        :return payment.transaction: The matching transaction record.
        :raises ValidationError: If no matching transaction is found.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'sadad' or len(tx) == 1:
            return tx

        # Try ORDERID (callback) first
        order_id = (
            notification_data.get('ORDERID')
            or notification_data.get('websiteRefNo')
            or notification_data.get('invoiceNumber')
            or ''
        )

        if not order_id:
            raise ValidationError(
                'SADAD: No order identifier found in notification data.'
            )

        # Search by stored sadad_order_id first
        tx = self.search([
            ('provider_code', '=', 'sadad'),
            ('sadad_order_id', '=', order_id),
        ])

        if not tx:
            # Fallback: try reference directly (for orders without prefix)
            tx = self.search([
                ('provider_code', '=', 'sadad'),
                ('reference', '=', order_id),
            ])

        if not tx:
            raise ValidationError(
                f'SADAD: No transaction found for order ID "{order_id}".'
            )

        return tx

    # -------------------------------------------------------------------------
    # Process notification — update transaction state
    # -------------------------------------------------------------------------

    def _process_notification_data(self, notification_data):
        """Update the transaction state based on SADAD callback/webhook data.

        Callback uses RESPCODE (1=success) and STATUS fields.
        Webhook uses transactionStatus (3=success, 2=failed).

        :param dict notification_data: Callback or webhook data.
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'sadad':
            return

        provider = self.provider_id

        # Verify signature before processing
        checksumhash = (
            notification_data.get('checksumhash')
            or notification_data.get('CHECKSUMHASH')
            or ''
        )

        if checksumhash:
            # Determine if this is a v1/webhook call (checksumhash is present)
            valid = provider._sadad_verify_signature_v1(notification_data, checksumhash)
            if not valid:
                _logger.warning(
                    'SADAD: Signature verification failed for transaction %s. '
                    'Notification data: %s',
                    self.reference, notification_data,
                )
                self._set_error('SADAD: Invalid payment signature.')
                return

        # Store transaction number
        txn_number = (
            notification_data.get('transaction_number')
            or notification_data.get('transactionNumber')
            or ''
        )
        if txn_number:
            self.sadad_transaction_number = txn_number

        # Store response codes
        self.sadad_response_code = str(notification_data.get('RESPCODE', ''))
        self.sadad_response_message = str(notification_data.get('RESPMSG', ''))

        # Determine success/failure
        # Callback: RESPCODE=1 and STATUS=TXN_SUCCESS
        resp_code = str(notification_data.get('RESPCODE', '')).strip()
        status = str(notification_data.get('STATUS', '')).strip().upper()

        # Webhook: transactionStatus=3 (success), 2 (failed), 1 (in progress)
        txn_status = int(notification_data.get('transactionStatus', 0))
        transaction_status_callback = int(notification_data.get('transaction_status', 0))

        is_success = (
            (resp_code == '1' and status == 'TXN_SUCCESS')
            or txn_status == 3
            or transaction_status_callback == 3
        )
        is_pending = (
            txn_status == 1
            or transaction_status_callback == 1
        )
        is_failed = (
            (resp_code and resp_code != '1')
            or status == 'TXN_FAILED'
            or txn_status == 2
            or transaction_status_callback == 2
        )

        if is_success:
            self._set_done()
        elif is_pending:
            self._set_pending()
        elif is_failed:
            self._set_canceled(
                state_message=self.sadad_response_message or 'Payment failed or cancelled.'
            )
        else:
            _logger.warning(
                'SADAD: Unrecognised notification status for transaction %s. Data: %s',
                self.reference, notification_data,
            )
            self._set_error('SADAD: Unrecognised payment status received.')

    # -------------------------------------------------------------------------
    # Refund — full refunds only, within 3 months
    # -------------------------------------------------------------------------

    def _sadad_refund(self, amount_to_refund=None):
        """Issue a full refund for this transaction via the SADAD API.

        SADAD supports FULL refunds only. Partial refunds are not supported.
        Refunds must be requested within 3 months of the transaction date.
        The transaction must have status 3 (Success).

        :param float amount_to_refund: Ignored — SADAD does full refunds only.
        :return dict: Result dict with 'success', and either 'data' or 'error'.
        """
        self.ensure_one()

        if self.provider_code != 'sadad':
            return {'success': False, 'error': 'Not a SADAD transaction.'}

        if not self.sadad_transaction_number:
            return {
                'success': False,
                'error': (
                    'Cannot refund: SADAD transaction number not available. '
                    'This usually means the payment was not confirmed by SADAD.'
                ),
            }

        if self.state != 'done':
            return {
                'success': False,
                'error': 'Cannot refund: Transaction is not in Done state.',
            }

        provider = self.provider_id

        # Step 1: Authenticate with SADAD API
        try:
            token = self._sadad_get_access_token(provider)
        except Exception as exc:
            _logger.error('SADAD refund auth failed for tx %s: %s', self.reference, exc)
            return {'success': False, 'error': f'Authentication failed: {exc}'}

        # Step 2: Submit refund request
        refund_url = f'{provider._get_sadad_api_url()}/transactions/refundTransaction'
        try:
            response = requests.post(
                refund_url,
                json={'transactionnumber': self.sadad_transaction_number},
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            _logger.info(
                'SADAD refund response for transaction %s: %s',
                self.reference, data,
            )
            return {'success': True, 'data': data}
        except requests.exceptions.Timeout:
            _logger.error('SADAD refund request timed out for tx %s', self.reference)
            return {'success': False, 'error': 'Refund request timed out.'}
        except requests.exceptions.RequestException as exc:
            _logger.error(
                'SADAD refund request failed for tx %s: %s', self.reference, exc
            )
            return {'success': False, 'error': str(exc)}

    @staticmethod
    def _sadad_get_access_token(provider):
        """Authenticate with SADAD API and return a bearer token.

        :param payment.provider provider: SADAD provider record.
        :return str: Bearer access token.
        :raises Exception: On authentication failure.
        """
        login_url = f'{provider._get_sadad_api_url()}/userbusinesses/login'
        response = requests.post(
            login_url,
            json={
                'sadadId': int(provider.sadad_merchant_id or 0),
                'secretKey': provider.sadad_secret_key or '',
                'domain': provider.sadad_website or '',
            },
            headers={'Content-Type': 'application/json'},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        token = data.get('accessToken') or data.get('access_token')
        if not token:
            raise Exception(f'No access token in SADAD auth response: {data}')
        return token

    # -------------------------------------------------------------------------
    # Override _send_refund_request for Odoo refund workflow integration
    # -------------------------------------------------------------------------

    def _send_refund_request(self, amount_to_refund=None):
        """Hook into Odoo's refund workflow for SADAD transactions.

        Called by Odoo core when a refund is initiated. Delegates to
        _sadad_refund for the actual API call.
        """
        if self.provider_code != 'sadad':
            return super()._send_refund_request(amount_to_refund=amount_to_refund)

        result = self._sadad_refund(amount_to_refund)
        if not result.get('success'):
            raise UserError(
                _('SADAD refund failed: %(error)s', error=result.get('error', 'Unknown error'))
            )
        return result
