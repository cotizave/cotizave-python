"""Basic usage of the Cotizave Python SDK.

Run it with your API key in the environment::

    export COTIZAVE_API_KEY="ctz_live_..."
    python examples/basic.py
"""

from __future__ import annotations

from cotizave import Cotizave, CotizaveError, RateLimitError


def main() -> None:
    # Reads COTIZAVE_API_KEY from the environment; or pass api_key="...".
    with Cotizave() as client:
        # Colombia's TRM, by its canonical id.
        trm = client.rates.get("CO", "co-trm")
        print("TRM:", trm.get("mid"))

        # Every rate published for a country.
        board = client.rates.list("AR")
        for rate in board["rates"]:
            print(rate["id"], "->", rate.get("mid"))

        # A conversion, resolved on Cotizave (never computed client-side).
        try:
            result = client.convert(from_="USD", to="BRL", amount=100)
            print("100 USD =", result["to"]["amount"], result["to"]["currency"])
        except RateLimitError as err:
            print("Rate limited:", "quota" if err.is_quota_exhausted else "slow down")
        except CotizaveError as err:
            print("API error:", err.status, err.code, err.message)

        # A short daily history series.
        series = client.history.daily("AR", "ar-official", from_="2026-09-01", to="2026-09-07")
        print("history points:", len(series.get("points", [])))


if __name__ == "__main__":
    main()
