"""thClaws Weather MCP — global weather via Open-Meteo.

Two tools exposed to the agent:
- `get_weather(location, days=1)`  — current conditions + N-day forecast
                                      for a city / lat,lng / postcode
- `geocode(query)`                  — resolve a place name to lat,lng,
                                      country (useful when the agent
                                      wants to confirm before fetching
                                      weather)

Open-Meteo is free and key-less for non-commercial use within their
fair-use limits (10,000 requests/day per IP at the time of writing).
For high-volume hosted deployments, sign up at https://open-meteo.com
and pass an API key via the `OPENMETEO_API_KEY` env var; the client
will switch to the commercial endpoint automatically.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# ── WMO weather code → human-readable label ──────────────────────────
# Open-Meteo returns weather as integer WMO codes; this table is the
# minimum needed to make the agent's output legible without forcing the
# model to memorize the spec.
# https://open-meteo.com/en/docs#weathervariables — "Weather variable
# documentation" → "WMO Weather interpretation codes (WW)".
WEATHER_CODES: dict[int, str] = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snow",
    73: "moderate snow",
    75: "heavy snow",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


def _label(code: int | None) -> str:
    if code is None:
        return "unknown"
    return WEATHER_CODES.get(int(code), f"code {code}")


def _api_base() -> tuple[str, str, dict[str, str]]:
    """Pick endpoint + auth header based on whether an API key is set.

    Returns (forecast_base, geocoding_base, params_to_inject).
    Open-Meteo's free endpoint takes no auth; the commercial endpoint
    accepts `apikey=<key>` as a query param. Always sign requests via
    query string (not headers) — Open-Meteo doesn't accept Authorization.
    """
    key = os.environ.get("OPENMETEO_API_KEY")
    if key:
        return (
            "https://customer-api.open-meteo.com/v1/forecast",
            "https://customer-api.open-meteo.com/v1/search",
            {"apikey": key},
        )
    return (
        "https://api.open-meteo.com/v1/forecast",
        "https://geocoding-api.open-meteo.com/v1/search",
        {},
    )


async def _geocode(client: httpx.AsyncClient, query: str) -> dict[str, Any] | None:
    """Resolve `query` (city name / postcode / 'lat,lng') to a place dict.

    Returns `None` when nothing matched. The Open-Meteo geocoding API
    returns `results: [...]` on a hit and an empty/missing key on miss.
    """
    # If the caller already passed `lat,lng`, skip geocoding.
    if "," in query:
        parts = [p.strip() for p in query.split(",", 1)]
        try:
            lat = float(parts[0])
            lng = float(parts[1])
            return {"latitude": lat, "longitude": lng, "name": query, "country": ""}
        except ValueError:
            pass  # fall through to text geocoding

    _, geo_base, extra = _api_base()
    params: dict[str, Any] = {
        "name": query,
        "count": 1,
        "language": "en",
        "format": "json",
    }
    params.update(extra)
    resp = await client.get(geo_base, params=params, timeout=10.0)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results") or []
    if not results:
        return None
    return results[0]


# ── MCP server ───────────────────────────────────────────────────────
mcp = FastMCP(
    "thclaws-weather",
    instructions=(
        "Provides global weather data via Open-Meteo. Use `get_weather` "
        "to retrieve current conditions plus a forecast for any location "
        "worldwide (city name, postcode, or 'lat,lng' coordinates). Use "
        "`geocode` separately if you need to confirm which place name "
        "the user means before fetching weather."
    ),
)


@mcp.tool()
async def geocode(query: str) -> str:
    """Resolve a place name (city / postcode / 'lat,lng') to coordinates.

    Returns a one-line summary including country so the caller can
    confirm the right place before requesting weather. Useful when the
    user typed an ambiguous name (e.g. "Springfield" — there are dozens).

    Args:
        query: Free-form place name. Examples: "Bangkok", "10110",
               "13.75,100.5", "Paris, France".
    """
    async with httpx.AsyncClient() as client:
        place = await _geocode(client, query)
    if place is None:
        return f"No match found for '{query}'."
    name = place.get("name", query)
    country = place.get("country", "")
    admin1 = place.get("admin1", "")
    lat = place.get("latitude")
    lng = place.get("longitude")
    where = ", ".join(p for p in (name, admin1, country) if p)
    return f"{where} — {lat:.4f}, {lng:.4f}"


@mcp.tool()
async def get_weather(location: str, days: int = 1) -> str:
    """Current weather + N-day forecast for any location worldwide.

    Args:
        location: City name, postcode, or 'lat,lng' coordinates. The
                  server geocodes free-form text first via Open-Meteo's
                  geocoding API; pass coords directly to skip that step.
        days: Forecast length in days (1-16, default 1). Day 1 is today.

    Returns:
        Human-readable summary: location confirmation, current conditions
        (temp, humidity, wind, weather), then per-day forecast (high/low,
        precipitation, weather).
    """
    days = max(1, min(int(days), 16))

    async with httpx.AsyncClient() as client:
        place = await _geocode(client, location)
        if place is None:
            return (
                f"Could not find '{location}'. Try a more specific name "
                "(e.g. 'Bangkok, Thailand') or pass 'lat,lng' coordinates."
            )

        lat = place["latitude"]
        lng = place["longitude"]
        name = place.get("name", location)
        country = place.get("country", "")
        place_label = f"{name}, {country}" if country else name

        forecast_base, _, extra = _api_base()
        params: dict[str, Any] = {
            "latitude": lat,
            "longitude": lng,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_sum,wind_speed_10m_max"
            ),
            "timezone": "auto",
            "forecast_days": days,
        }
        params.update(extra)
        resp = await client.get(forecast_base, params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()

    # ── format ────────────────────────────────────────────────────────
    cur = data.get("current", {})
    cur_units = data.get("current_units", {})
    daily = data.get("daily", {})

    lines: list[str] = []
    lines.append(f"Weather for {place_label} ({lat:.2f}, {lng:.2f}):")
    if cur:
        temp = cur.get("temperature_2m")
        hum = cur.get("relative_humidity_2m")
        wind = cur.get("wind_speed_10m")
        code = cur.get("weather_code")
        temp_u = cur_units.get("temperature_2m", "°C")
        wind_u = cur_units.get("wind_speed_10m", "km/h")
        lines.append(
            f"  Now: {temp}{temp_u}, {_label(code)}, "
            f"humidity {hum}%, wind {wind} {wind_u}"
        )

    times = daily.get("time", [])
    codes = daily.get("weather_code", [])
    highs = daily.get("temperature_2m_max", [])
    lows = daily.get("temperature_2m_min", [])
    precs = daily.get("precipitation_sum", [])
    winds = daily.get("wind_speed_10m_max", [])
    if times:
        daily_units = data.get("daily_units", {})
        t_unit = daily_units.get("temperature_2m_max", "°C")
        p_unit = daily_units.get("precipitation_sum", "mm")
        w_unit = daily_units.get("wind_speed_10m_max", "km/h")
        lines.append("  Forecast:")
        for i, date in enumerate(times):
            high = highs[i] if i < len(highs) else None
            low = lows[i] if i < len(lows) else None
            code = codes[i] if i < len(codes) else None
            prec = precs[i] if i < len(precs) else None
            wind = winds[i] if i < len(winds) else None
            lines.append(
                f"    {date}: {low}–{high}{t_unit}, {_label(code)}, "
                f"rain {prec}{p_unit}, wind ≤ {wind} {w_unit}"
            )

    return "\n".join(lines)


def main() -> None:
    """Entry point for the `thclaws-weather` console script.

    Transport defaults to stdio (the standard MCP install pattern); set
    MCP_TRANSPORT=sse + MCP_PORT=<n> to expose over HTTP for the k3s
    hosted deployment instead.
    """
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "sse":
        # FastMCP's built-in SSE transport. Reads MCP_PORT or defaults
        # to 8000; bind 0.0.0.0 so the cluster Service can reach it.
        port = int(os.environ.get("MCP_PORT", "8000"))
        mcp.settings.host = "0.0.0.0"
        mcp.settings.port = port
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
