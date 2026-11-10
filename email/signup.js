/* Native POST is authoritative. This script only improves validation feedback. */
(function () {
  'use strict';
  document.querySelectorAll('form[data-newsletter-signup]').forEach(function (form) {
    var input = form.querySelector('input[type="email"]');
    var message = form.querySelector('[data-signup-message]');
    if (!input || !message) return;
    input.addEventListener('invalid', function () {
      input.setAttribute('aria-invalid', 'true');
      message.textContent = 'Please enter a valid email address.';
    });
    input.addEventListener('input', function () {
      input.removeAttribute('aria-invalid');
      message.textContent = '';
    });
    // Do not intercept submission, queue addresses, fetch a provider endpoint,
    // or claim success. The browser submits to AWeber and displays its response.
  });
})();
