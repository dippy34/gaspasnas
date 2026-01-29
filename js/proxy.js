/**
 * Proxy URL normalization for Nova Hub.
 * - If no https:// (or http://) before link: add https:// and lowercase.
 * - If there are spaces or no valid TLD ending: use Google search (spaces → %20 in query).
 * - Works on localhost and production.
 */
(function () {
	'use strict';

	/** Known TLDs for "has valid URL ending" check */
	var TLD_LIST = 'com|dev|net|edu|org|gov|io|co|app|xyz|info|me|us|uk|eu|au|ca|in|de|fr|jp|cn|tv|cc|ru|br|es|it|nl|pl';
	var TLD_PATTERN = new RegExp('\\.(' + TLD_LIST + ')([\\s\\/\\?#"\']|$)', 'i');

	/**
	 * Normalize user input into a full URL (or Google search URL).
	 * - No https:// → add https:// and lowercase.
	 * - Spaces or no valid TLD (.com, .dev, .net, .edu, .org, .gov, etc.) → Google search (spaces as %20).
	 * @param {string} input - Raw input from the URL bar
	 * @returns {string} Final URL to load
	 */
	function normalizeUrl(input) {
		if (typeof input !== 'string') return 'https://www.google.com/';
		var raw = input.trim();
		if (!raw) return 'https://www.google.com/';

		var hasSpaces = /\s/.test(raw);
		var hasValidTld = TLD_PATTERN.test(raw);

		// If there are spaces or no valid TLD ending → Google search; spaces become %20 via encodeURIComponent
		if (hasSpaces || !hasValidTld) {
			return 'https://www.google.com/search?q=' + encodeURIComponent(raw);
		}

		// Treat as URL: ensure scheme and lowercase
		var lower = raw.toLowerCase();
		if (!/^https?:\/\//i.test(lower)) {
			lower = 'https://' + lower;
		}
		return lower;
	}

	/**
	 * Resolve proxy base URL (works on localhost and production).
	 * Returns origin so the iframe can load relative proxy routes or same-origin gateways.
	 */
	function getBaseUrl() {
		return window.location.origin;
	}

	// Expose for use in proxy page
	window.NovaProxy = {
		normalizeUrl: normalizeUrl,
		getBaseUrl: getBaseUrl
	};
})();
