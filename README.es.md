<div align="center">

[English](./README.md) · **Español**

# SDK de Python de Cotizave

Cliente oficial de Python, totalmente tipado, para la **API v2 de Cotizave** —
tasas de cambio multipaís, conversión de monedas, series históricas, tasas de
bancos y calendarios, con una sola API key.

[![PyPI](https://img.shields.io/pypi/v/cotizave?color=3775A9&logo=pypi&logoColor=white)](https://pypi.org/project/cotizave/)
[![Python](https://img.shields.io/pypi/pyversions/cotizave)](https://pypi.org/project/cotizave/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

[Hub de API y docs](https://github.com/cotizave/exchange-rates-api) · [Documentación](https://docs.cotizave.com) · [Referencia de la API](https://docs.cotizave.com/api/v2/introduction) · [Obtené una API key](https://app.cotizave.com)

</div>

---

## Instalación

```bash
pip install cotizave
```

Requiere Python 3.10+. La única dependencia en runtime es [httpx](https://www.python-httpx.org/).

## Inicio rápido

```python
from cotizave import Cotizave

# Lee COTIZAVE_API_KEY del entorno; o pasá api_key="..."
client = Cotizave()

# Todas las tasas publicadas de un país
response = client.rates.list("AR")
for rate in response["rates"]:
    print(rate["id"], rate.get("mid"))

# Una tasa por su id canónico
trm = client.rates.get("CO", "co-trm")
print(trm["mid"])

# Una conversión (resuelta en Cotizave, nunca en el cliente)
result = client.convert(from_="USD", to="BRL", amount=100)
print(result["to"]["amount"])

client.close()
```

Usalo como context manager para cerrar el pool de conexiones automáticamente:

```python
with Cotizave() as client:
    feed = client.rates.global_(symbols=["BRL", "EUR"])
```

> **Mantené tu API key del lado del servidor.** Se envía solo en la cabecera
> `X-API-Key`. Nunca la incluyas en un bundle de navegador, una app móvil ni
> ningún cliente público.

## Autenticación

Pasá la key explícitamente o dejá que el cliente la lea del entorno:

```python
client = Cotizave(api_key="ctz_live_...")  # explícita
client = Cotizave()  # desde COTIZAVE_API_KEY
```

## Qué podés hacer

| Área | Llamada |
| --- | --- |
| Tasas de un país | `client.rates.list("CO")` |
| Una tasa por id | `client.rates.get("CO", "co-trm")` |
| Tablero pasado de un país | `client.rates.snapshot("AR", "2026-10-01")` |
| Oficial de cada país | `client.rates.global_(symbols=["BRL", "EUR"])` |
| Convertir un monto | `client.convert(from_="USD", to="BRL", amount=100)` |
| Convertir hasta 50 montos | `client.convert_bulk([...])` |
| Histórico puntual | `client.history.get("CO", "co-trm", "2026-10-01")` |
| Serie histórica diaria | `client.history.daily("AR", "ar-official", from_="2026-09-01", to="2026-09-30")` |
| Estadísticas del período | `client.history.stats("AR", "ar-official", from_="...", to="...", moving_average=7)` |
| Capturas crudas (paginadas) | `client.history.raw(...)` / `client.history.iterate(...)` |
| Cobertura del histórico | `client.history.limits()` |
| Catálogo de tasas | `client.markets("VE")` |
| Brecha vs otra tasa | `client.spread("VE", against="ve-paralelo")` |
| Mejor ruta ejecutable | `client.route("VE", from_="USD", to="VES", amount=100)` |
| Tasas por banco | `client.bank_rates("VE")` |
| Países / monedas | `client.countries.list()` · `client.currencies.list()` |
| Bancos / emisores | `client.banks.list("VE")` · `client.issuers.list()` |
| Feriados y días hábiles | `client.holidays.list("AR")` · `client.holidays.business_days("VE", from_="2026-10-01", days=5)` |
| Estables (USD) | `client.crypto.list()` · `client.crypto.get("usdt-usd")` |

Las respuestas son `dict` planos, tipados con `TypedDict` para autocompletado. Los
campos presentes dependen de tu plan, el país y el mercado — leelos con `.get(...)`
y consultá la [referencia de la API](https://docs.cotizave.com/api/v2/introduction).

## Errores

Cada fallo lanza una subclase de `CotizaveError`. Capturá la base para cualquier
error de la API, o una subclase para una familia específica:

```python
from cotizave import Cotizave, RateLimitError, NotFoundError, CotizaveError

client = Cotizave()
try:
    rate = client.rates.get("CO", "co-trm")
except RateLimitError as err:
    if err.is_quota_exhausted:
        print("Cuota mensual agotada")
    else:
        print(f"Bajá el ritmo; reintentá en {err.retry_after}s")
except NotFoundError:
    print("No existe esa tasa")
except CotizaveError as err:
    print(err.status, err.code, err.message)
```

| Excepción | HTTP |
| --- | --- |
| `BadRequestError` | 400 |
| `AuthenticationError` | 401 |
| `FeatureNotInPlanError` | 402 |
| `ForbiddenError` | 403 |
| `NotFoundError` | 404 |
| `NotAcceptableError` | 406 |
| `UnprocessableError` | 422 |
| `RateLimitError` | 429 |
| `ServerError` | 5xx |
| `APIConnectionError` / `APITimeoutError` | sin respuesta (red/timeout) |

Cada error lleva `status`, `code`, `message`, `field`/`details` opcionales, y
`rate_limit` / `headers` / `request_id` de la respuesta.

## Configuración

Todo tiene un valor por defecto seguro para producción; sobreescribí solo lo que necesites:

```python
from cotizave import Cotizave, RetryOptions

client = Cotizave(
    api_key="ctz_live_...",
    timeout=5.0,  # timeout por petición, en segundos
    history_timeout=10.0,  # timeout más largo para lecturas de histórico
    max_retries=2,  # reintentos extra para peticiones elegibles
    max_retry_delay=10.0,  # presupuesto total de backoff por llamada, en segundos
    max_response_bytes=25_000_000,
    language="es",  # Accept-Language para nombres localizados
    headers={"X-Trace-Id": "..."},
    retry=RetryOptions(
        base_delay=0.25,
        max_delay=2.0,
        retry_rate_limited=True,
        on_retry=lambda e: print("reintentando", e.path, "en", e.delay, "s"),
    ),
    on_response=lambda e: print(e.meta.status, e.meta.rate_limit.remaining),
)
```

Cada método acepta overrides por llamada (`timeout`, `max_retries`, `headers`, `language`):

```python
client.rates.list("AR", timeout=2.0, max_retries=0)
```

### Política de reintentos

Solo se reintentan peticiones idempotentes (GET). Un `429` se reintenta solo
cuando es un límite de velocidad (por minuto), respetando el `Retry-After` del
servidor; un `429` por cuota mensual agotada nunca se reintenta. Los errores de
conexión y timeout, y los 5xx configurados, se reintentan con backoff exponencial
y jitter completo, acotados por `max_retries` y el presupuesto `max_retry_delay`.

## Exportar CSV / XML

```python
csv = client.export("/v2/fx/ar/rates", format="csv")
```

## Peticiones de bajo nivel

Para lo que los recursos tipados no cubren, incluyendo GET condicionales y
metadatos de respuesta:

```python
result = client.request(method="GET", path="/v2/fx/co/rates/co-trm", if_none_match='"abc"')
print(result.not_modified, result.meta.status, result.data)
```

## Seguridad

- La API key se envía solo en la cabecera `X-API-Key` y nunca se expone en
  `client.config`, en `repr()` ni al loguear el cliente.
- Cada petición queda fijada al origen configurado; un path que resuelve a otro
  host se rechaza, y los redirects nunca se siguen — así la key no puede filtrarse
  a otro origen.
- El cuerpo de la respuesta se limita a `max_response_bytes` para protegerte de
  una respuesta sobredimensionada o una bomba de descompresión.

¿Encontraste un problema de seguridad? Mirá [SECURITY.md](./SECURITY.md).

## Licencia

[MIT](./LICENSE)
