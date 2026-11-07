# Security Policy

## Reporting a vulnerability

Please report security issues privately. **Do not open a public GitHub issue for
a vulnerability.**

- Email: **security@cotizave.com**
- Or use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
  on this repository.

Include a description, reproduction steps, affected versions, and impact. We aim
to acknowledge within a few business days and will coordinate a fix and
disclosure timeline with you.

## Handling API keys

This SDK is designed for **server-side** use.

- Never embed a private API key in a browser bundle, a mobile app, or any
  client-side code.
- Load the key from a server-side secret (environment variable or secret
  manager), never from source control.
- The client reads `COTIZAVE_API_KEY` from the environment when no `api_key` is
  passed, so the key never needs to appear in your source.

The SDK sends your key only as the `X-API-Key` header to the configured
`base_url`, never in a URL or query string. It is not exposed on `client.config`,
in `repr()`, or in error messages; the SDK does not log the key, persist it, or
send telemetry.

## Transport hardening

- **Origin pinning.** Every request is pinned to the configured origin. A path
  that resolves to a different host is refused (`invalid_request_path`), so a
  crafted path cannot send your key elsewhere.
- **No redirects.** Redirects are never followed; a redirect response is turned
  into an error (`unexpected_redirect`), preventing the key from being forwarded
  to another origin.
- **HTTPS required.** A non-HTTPS `base_url` is rejected unless you explicitly
  set `allow_insecure_http=True` (intended only for local testing).
- **Response-size cap.** Bodies are capped at `max_response_bytes` (default
  25 MB) to guard against an oversized or decompression-bomb response.

## Supply chain

- The package has a single runtime dependency: [httpx](https://www.python-httpx.org/)
  (BSD-3-Clause).
- Releases are built on GitHub-hosted runners and published to PyPI with
  [Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/) — no
  long-lived API token is stored.

## Supported versions

The latest released version receives security fixes. Pin a version and upgrade
promptly when a security release is published.
