# Changelog

All notable changes to this project are documented here. This project adheres
to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Initial release of the official Python SDK for the Cotizave API v2.
- Synchronous `Cotizave` client with typed resources: `rates`, `history`,
  `countries`, `currencies`, `banks`, `issuers`, `holidays`, `crypto`, plus
  top-level `convert`, `convert_bulk`, `markets`, `spread`, `route` and
  `bank_rates`.
- Typed error hierarchy (`CotizaveError` and subclasses), controlled retries
  with full jitter and a time budget, response-size cap, origin pinning and
  redirect refusal to protect the API key.
- `TypedDict` response shapes and a `py.typed` marker (PEP 561).
