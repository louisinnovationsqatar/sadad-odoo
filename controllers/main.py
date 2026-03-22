# Built by Louis Innovations (www.louis-innovations.com)
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SadadController(http.Controller):
    """HTTP controllers for SADAD callback and webhook endpoints.

    Two endpoints are registered:
    - /payment/sadad/callback  — POST redirect after customer completes payment
    - /payment/sadad/webhook   — JSON POST notification from SADAD server

    Built by Louis Innovations (www.louis-innovations.com)
    """

    _callback_url = '/payment/sadad/callback'
    _webhook_url = '/payment/sadad/webhook'

    @http.route(
        _callback_url,
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
        save_session=False,
    )
    def sadad_callback(self, **post):
        """Handle SADAD callback redirect after payment.

        SADAD redirects the customer's browser to this URL after checkout.
        POST params include: website_ref_no, transaction_status, transaction_number,
        MID, RESPCODE, RESPMSG, ORDERID, STATUS, TXNAMOUNT, checksumhash.

        On success/failure the customer is redirected to /payment/status.
        """
        _logger.info('SADAD: Callback received. Params: %s', post)

        try:
            tx_sudo = request.env['payment.transaction'].sudo()
            tx = tx_sudo._get_tx_from_notification_data('sadad', post)
            tx._handle_notification_data('sadad', post)
        except Exception as exc:
            _logger.exception(
                'SADAD: Exception processing callback data %s: %s', post, exc
            )

        # Always redirect to payment status page regardless of outcome
        return request.redirect('/payment/status')

    @http.route(
        _webhook_url,
        type='json',
        auth='public',
        methods=['POST'],
        csrf=False,
        save_session=False,
    )
    def sadad_webhook(self, **kwargs):
        """Handle SADAD server-to-server webhook notification.

        SADAD POSTs a JSON body with fields:
        invoiceNumber, isTestMode, merchantId, message, transactionNumber,
        transactionStatus, txnAmount, websiteRefNo, checksumhash.

        Must return HTTP 200 with JSON body: {"status": "success"}.
        """
        try:
            raw_data = request.httprequest.data
            data = json.loads(raw_data)
            _logger.info('SADAD: Webhook received. Data: %s', data)

            tx_sudo = request.env['payment.transaction'].sudo()
            tx = tx_sudo._get_tx_from_notification_data('sadad', data)
            tx._handle_notification_data('sadad', data)
        except json.JSONDecodeError as exc:
            _logger.error('SADAD: Invalid JSON in webhook body: %s', exc)
            return {'status': 'error', 'message': 'Invalid JSON'}
        except Exception as exc:
            _logger.exception('SADAD: Exception processing webhook: %s', exc)
            # Still return success to prevent SADAD from retrying indefinitely
            return {'status': 'success'}

        return {'status': 'success'}
