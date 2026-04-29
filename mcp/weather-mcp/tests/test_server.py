"""Smoke tests for thclaws-weather.

These tests don't hit the real Open-Meteo API — they patch httpx so the
suite is fast, deterministic, and works offline (e.g. in CI sandboxes
without network egress). The "happy path actually-calls-Open-Meteo"
test is left as a manual integration smoke (run `python -m
thclaws_weather` and ask an MCP client for `get_weather Bangkok`).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from thclaws_weather.server import _label, geocode, get_weather


def test_wmo_code_label_known() -> None:
    assert _label(0) == "clear sky"
    assert _label(95) == "thunderstorm"
    assert _label(99) == "thunderstorm with heavy hail"


def test_wmo_code_label_unknown() -> None:
    # Open-Meteo guarantees only the documented codes; an unknown code
    # falls back to "code <n>" rather than crashing the formatter.
    assert _label(404) == "code 404"
    assert _label(None) == "unknown"


@pytest.mark.asyncio
async def test_geocode_with_coords_string_skips_api() -> None:
    """`'13.75,100.5'` is detected as coordinates and returned without
    calling Open-Meteo at all — saves a round-trip when the agent
    already has lat/lng."""
    with patch("thclaws_weather.server.httpx.AsyncClient") as mock_client:
        result = await geocode.fn("13.75,100.5")
    # The client was constructed but no .get call happened on the
    # geocoding endpoint (the early-return path).
    instance = mock_client.return_value.__aenter__.return_value
    instance.get.assert_not_called()
    assert "13.7500" in result
    assert "100.5000" in result


@pytest.mark.asyncio
async def test_get_weather_no_match() -> None:
    """Open-Meteo returns `results: []` when nothing matches; the tool
    should produce a helpful nudge, not a stack trace."""
    fake_response = AsyncMock()
    fake_response.raise_for_status = lambda: None
    fake_response.json = lambda: {"results": []}

    fake_get = AsyncMock(return_value=fake_response)

    with patch("thclaws_weather.server.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = fake_get
        out = await get_weather.fn("zzzznotaplace", days=1)

    assert "Could not find" in out
    assert "lat,lng" in out  # nudge user toward coords path
