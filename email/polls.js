/* Votes are sent only after a reader explicitly confirms. Never submit on load. */
(function () {
  'use strict';
  var endpoint = 'https://energized-kiwi-650.convex.site/v1/votes';
  var storageKey = 'ws-poll-voter';
  var lifetime = 30 * 24 * 60 * 60 * 1000;
  var msg = document.getElementById('msg');
  var question = document.getElementById('poll-question');
  var button = document.getElementById('confirm-vote');
  if (!msg || !question || !button) return;

  var params = new URLSearchParams(location.search);
  var poll = params.get('poll'), vote = params.get('vote');
  if (params.getAll('poll').length !== 1 || params.getAll('vote').length !== 1 ||
      !poll || poll.length > 100 || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(poll) ||
      (vote !== 'yes' && vote !== 'no')) {
    msg.textContent = 'This poll link is invalid or unavailable. No vote was sent. Please return to the edition and select Yes or No.';
    return;
  }
  // The backend registry owns daily poll definitions. Never hardcode news here.
  question.textContent = 'World Skim reader poll';
  msg.textContent = 'You selected ' + (vote === 'yes' ? 'Yes' : 'No') + '. Your vote has not been recorded. Confirm below to submit it.';
  button.textContent = 'Confirm ' + (vote === 'yes' ? 'Yes' : 'No') + ' vote';
  button.hidden = false;
  button.style.display = '';
  button.disabled = false;
  var pending = false, finished = false, voter = null, storageFailed = false;

  function identity() {
    if (storageFailed) throw new Error('storage');
    if (voter) return voter;
    try {
      if (!window.crypto || typeof window.crypto.getRandomValues !== 'function') throw new Error('crypto');
      var raw = localStorage.getItem(storageKey), saved = raw ? JSON.parse(raw) : null;
      var now = Date.now();
      if (saved && (!/^[0-9a-f]{32}$/.test(saved.voter) ||
          !Number.isFinite(saved.expires) || saved.expires > now + lifetime)) throw new Error('storage');
      if (!saved || saved.expires <= now) {
        var bytes = new Uint8Array(16);
        window.crypto.getRandomValues(bytes);
        saved = { voter: Array.from(bytes, function (b) { return b.toString(16).padStart(2, '0'); }).join(''), expires: now + lifetime };
      }
      var serialized = JSON.stringify(saved);
      localStorage.setItem(storageKey, serialized);
      if (localStorage.getItem(storageKey) !== serialized) throw new Error('storage');
      voter = saved.voter;
      return voter;
    } catch (error) {
      storageFailed = true;
      throw error;
    }
  }

  button.addEventListener('click', async function (event) {
    if (!event.isTrusted || pending || finished || storageFailed) return;
    pending = true;
    button.disabled = true;
    var nonce;
    try {
      nonce = identity();
    } catch (error) {
      msg.textContent = 'This browser cannot securely save an anonymous voting token. No vote was sent. Allow local storage and secure browser features, then reload this page.';
      pending = false;
      return;
    }
    msg.textContent = 'Submitting your vote. Please wait for confirmation.';
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, 15000);
    try {
      var response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'omit',
        referrerPolicy: 'no-referrer',
        cache: 'no-store',
        signal: controller.signal,
        body: JSON.stringify({ brand: 'worldskim', poll: poll, vote: vote, voter: nonce })
      });
      var result = await response.json();
      if (result && result.ok !== true) {
        if (result.error === 'poll_closed' || result.error === 'unknown_poll') {
          msg.textContent = result.error === 'poll_closed'
            ? 'This poll is closed. No vote was confirmed.'
            : 'This poll is unavailable. No vote was confirmed. Please return to the edition.';
          finished = true;
          button.hidden = true;
          button.style.display = 'none';
          return;
        }
        if (result.error === 'voting_disabled' || result.error === 'poll_capacity_reached') {
          msg.textContent = 'Voting is temporarily unavailable. No vote was confirmed. Please try again later.';
          button.textContent = 'Retry confirmation';
          button.disabled = false;
          return;
        }
      }
      if (!response.ok || result.ok !== true || typeof result.duplicate !== 'boolean' ||
          (result.vote !== 'yes' && result.vote !== 'no') ||
          (!result.duplicate && result.vote !== vote)) throw new Error('unconfirmed');
      var storedVote = result.vote === 'yes' ? 'Yes' : 'No';
      msg.textContent = result.duplicate
        ? 'You already voted ' + storedVote + ' in this poll. Your original vote is unchanged and was not counted again.'
        : 'Your ' + storedVote + ' vote was recorded. Thank you for taking part.';
      finished = true;
      button.hidden = true;
      button.style.display = 'none';
    } catch (error) {
      msg.textContent = 'We could not confirm your vote. It may not have been recorded. Retry in this browser to safely check without counting twice.';
      button.textContent = 'Retry confirmation';
      button.disabled = false;
    } finally {
      clearTimeout(timer);
      pending = false;
    }
  });
})();
