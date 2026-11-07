"""Official Python SDK for the Cotizave API v2.

Example::

    from cotizave import Cotizave

    client = Cotizave()  # reads COTIZAVE_API_KEY from the environment
    response = client.rates.list("AR")
"""

from __future__ import annotations

from ._transport import RawResult
from ._version import __version__
from .client import Cotizave
from .config import (
    API_KEY_ENV_VAR,
    DEFAULT_BASE_URL,
    DEFAULT_HISTORY_TIMEOUT,
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_RETRY_DELAY,
    DEFAULT_TIMEOUT,
    PublicConfig,
    ResponseEvent,
    RetryContext,
    RetryEvent,
    RetryOptions,
)
from .errors import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    CotizaveError,
    FeatureNotInPlanError,
    ForbiddenError,
    NotAcceptableError,
    NotFoundError,
    RateLimitError,
    RateLimitInfo,
    ResponseMeta,
    ServerError,
    UnprocessableError,
)
from .resources import BULK_CONVERT_MAX

__all__ = [
    "__version__",
    "Cotizave",
    # config
    "API_KEY_ENV_VAR",
    "DEFAULT_BASE_URL",
    "DEFAULT_TIMEOUT",
    "DEFAULT_HISTORY_TIMEOUT",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_MAX_RETRY_DELAY",
    "DEFAULT_MAX_RESPONSE_BYTES",
    "BULK_CONVERT_MAX",
    "PublicConfig",
    "RetryOptions",
    "RetryContext",
    "RetryEvent",
    "ResponseEvent",
    "RawResult",
    # errors
    "CotizaveError",
    "BadRequestError",
    "AuthenticationError",
    "FeatureNotInPlanError",
    "ForbiddenError",
    "NotFoundError",
    "NotAcceptableError",
    "UnprocessableError",
    "RateLimitError",
    "ServerError",
    "APIConnectionError",
    "APITimeoutError",
    "RateLimitInfo",
    "ResponseMeta",
]
