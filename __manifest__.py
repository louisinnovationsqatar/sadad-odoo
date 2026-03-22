# Built by Louis Innovations (www.louis-innovations.com)
{
    'name': 'SADAD Payment Gateway',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Accept payments via SADAD Payment Gateway (Qatar) - Free & Open Source',
    'description': """
SADAD Payment Gateway integration for Odoo eCommerce.

Supports Web Checkout v1.1, v2.1, and v2.2 modes.
Free, open-source alternative to proprietary SADAD modules.

Features:
- Web Checkout v1.1 (classic redirect with SHA-256 signature)
- Web Checkout v2.1 (enhanced redirect with AES-128-CBC checksum)
- Web Checkout v2.2 (embedded payment form with AES-128-CBC checksum)
- Full refund support via SADAD API
- Webhook notifications
- Multi-language (English/Arabic)
- Transaction logging

Built by Louis Innovations (www.louis-innovations.com)
    """,
    'author': 'Louis Innovations',
    'website': 'https://www.louis-innovations.com',
    'license': 'LGPL-3',
    'depends': ['payment', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_provider_data.xml',
        'views/payment_provider_views.xml',
        'views/payment_sadad_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_sadad/static/src/js/payment_form.js',
            'payment_sadad/static/src/css/payment_sadad.css',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    # Odoo version compatibility notes:
    # 17.0 (primary): Full support
    # 16.0: Compatible — payment.provider API is the same; test before deploying
    # 18.0: Should be compatible — verify payment module API changes
}
