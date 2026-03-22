/** @odoo-module **/
// Built by Louis Innovations (www.louis-innovations.com)

/**
 * SADAD Payment Form JS
 *
 * Handles:
 * - Auto-submit of the redirect form on page load (v1.1 and v2.1 modes)
 * - POST + iframe load for embedded mode (v2.2)
 * - Error/timeout handling with user-facing fallback button
 */

import { Component, onMounted } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

const SADAD_REDIRECT_DELAY_MS = 800;
const SADAD_REDIRECT_TIMEOUT_MS = 10000;

/**
 * Auto-submit the SADAD redirect form after a short delay.
 * Shows the spinner during the delay, then submits.
 * If submission takes too long, the fallback button becomes visible.
 */
function initSadadRedirect() {
    const form = document.getElementById("sadad_redirect_form");
    const spinner = document.querySelector(".sadad-spinner");
    const fallbackBtn = document.querySelector(".sadad-manual-submit");

    if (!form) return;

    // Auto-submit after short delay to let page render
    const submitTimer = setTimeout(() => {
        try {
            form.submit();
        } catch (e) {
            // eslint-disable-next-line no-console
            console.error("SADAD: form submit failed:", e);
            if (fallbackBtn) fallbackBtn.style.display = "inline-block";
        }
    }, SADAD_REDIRECT_DELAY_MS);

    // Show fallback button if redirect hasn't happened after timeout
    setTimeout(() => {
        clearTimeout(submitTimer);
        if (spinner) spinner.style.display = "none";
        if (fallbackBtn) fallbackBtn.style.display = "inline-block";
    }, SADAD_REDIRECT_TIMEOUT_MS);
}

/**
 * Submit the embedded form and load into the SADAD iframe.
 */
function initSadadEmbedded() {
    const form = document.getElementById("sadad_embedded_form");
    const iframe = document.getElementById("sadad_iframe");

    if (!form || !iframe) return;

    // Submit on next tick so iframe is ready
    setTimeout(() => {
        form.submit();
    }, 100);

    // Adjust iframe height on load
    iframe.addEventListener("load", () => {
        try {
            iframe.style.height = "600px";
        } catch (e) {
            // Cross-origin: cannot access contentDocument height
        }
    });
}

/**
 * Main initialiser — detects mode and wires up the appropriate flow.
 */
function initSadadPaymentForm() {
    const container = document.getElementById("sadad_payment_form");
    if (!container) return;

    const isEmbedded = container.querySelector(".sadad-embedded-container") !== null;

    if (isEmbedded) {
        initSadadEmbedded();
    } else {
        initSadadRedirect();
    }
}

// Initialise when DOM is ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSadadPaymentForm);
} else {
    initSadadPaymentForm();
}

export default { initSadadPaymentForm };
