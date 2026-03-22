# Contributing to SADAD Payment Gateway for Odoo

Thank you for considering contributing to this project!
Built by Louis Innovations (www.louis-innovations.com)

---

## How to Contribute

### Reporting Bugs

1. Check existing [GitHub Issues](https://github.com/louis-innovations/payment_sadad/issues) first
2. Create a new issue with:
   - Odoo version
   - SADAD checkout mode (v1.1 / v2.1 / v2.2)
   - Steps to reproduce
   - Expected vs actual behaviour
   - Relevant Odoo server logs

### Suggesting Features

Open a GitHub Issue with the "Feature Request" template.

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Write clean, documented code following Odoo conventions
4. Test with a real Odoo instance and SADAD test credentials
5. Update documentation if needed
6. Submit a pull request against the `main` branch

---

## Code Standards

- Follow Odoo's Python coding guidelines
- All user-facing strings must use `_()` for translation
- Add docstrings to all public methods
- No hardcoded credentials or secrets
- No breaking changes to existing API without deprecation notice
- Preserve the "Built by Louis Innovations" comment in all Python files

---

## Testing

Before submitting:
1. Test with Odoo 17.0 (primary target)
2. Test all three checkout modes (v1.1, v2.1, v2.2)
3. Test callback and webhook processing
4. Test refund flow
5. Verify Arabic language checkout works
6. Check Odoo server logs for errors or warnings

---

## License

By contributing, you agree your contributions will be licensed under LGPL-3.

---

*Built by Louis Innovations (www.louis-innovations.com)*
