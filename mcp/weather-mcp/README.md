# thClaws Weather MCP

Global weather MCP server. **No API key required.** Works for any city, postcode, or `lat,lng` worldwide — replaces the US-only NWS-based servers.

Powered by [Open-Meteo](https://open-meteo.com), a free, key-less, fair-use weather API with global coverage. For high-volume hosted deployments, set `OPENMETEO_API_KEY` and the server switches to Open-Meteo's commercial endpoint automatically.

This is also the first reference MCP for the thClaws marketplace — copy this directory as the template for your own MCP.

## Tools

| Tool | Args | Returns |
|---|---|---|
| `get_weather` | `location` (string), `days` (int, 1-16, default 1) | Current conditions + forecast — formatted summary |
| `geocode` | `query` (string) | One-line `name, region, country — lat, lng` |

The `location` argument accepts city names (`"Bangkok"`), postcodes (`"10110"`), `lat,lng` coordinates (`"13.75,100.5"`), or qualified queries (`"Paris, France"`). Geocoding happens automatically via Open-Meteo's geocoding API; coordinate strings are detected and skip that step.

## Install

### Local (stdio) — for thClaws / Claude Code / any MCP client

```bash
# Install from source (PyPI publish pending):
git clone https://github.com/thClaws/marketplace.git
cd marketplace/mcp/weather-mcp
pip install -e .
```

Then add to `~/.config/thclaws/mcp.json`:

```json
{
  "mcpServers": {
    "weather": {
      "command": "thclaws-weather"
    }
  }
}
```

…or via the thClaws slash command (when the MCP marketplace ships in v0.7.0):

```
/mcp install --user weather-mcp
```

### Hosted (HTTP/SSE) — for shared cluster deployments

The same server runs in SSE mode by setting two env vars:

```bash
MCP_TRANSPORT=sse MCP_PORT=8000 thclaws-weather
```

A `Dockerfile` is provided for k3s deployment — see [`infra/k3s/thclaws-mcp/`](https://github.com/JimmySoftware/agentic-workspace/tree/main/infra/k3s/thclaws-mcp) in the workspace for the matching Deployment + IngressRoute manifests. After deploy:

```
https://weather-mcp.artech.cloud/sse
```

…and the marketplace catalog (when it ships) lists this URL as the `install_url` for users who want to use the hosted MCP without local install.

## Example session

```
You: What's the weather in Bangkok this week?

Agent: Weather for Bangkok, Thailand (13.75, 100.52):
  Now: 32.4°C, partly cloudy, humidity 68%, wind 11.2 km/h
  Forecast:
    2026-04-29: 26.1–34.8°C, thunderstorm, rain 5.4 mm, wind ≤ 18 km/h
    2026-04-30: 25.8–35.2°C, partly cloudy, rain 0 mm, wind ≤ 15 km/h
    ...
```

## Configuration

| Env var | Purpose | Default |
|---|---|---|
| `MCP_TRANSPORT` | `stdio` for local install, `sse` for HTTP/SSE hosting | `stdio` |
| `MCP_PORT` | Port for SSE transport | `8000` |
| `OPENMETEO_API_KEY` | Optional Open-Meteo commercial API key for high-volume deployments | (unset → free endpoint) |

## Fair-use limits (free endpoint)

Open-Meteo's free tier is generous for individual / small-team use:
- ~10,000 requests per day per IP
- No API key, no signup
- Non-commercial use within fair-use terms

For higher limits or commercial guarantees, [sign up at open-meteo.com](https://open-meteo.com/en/pricing) and pass the key via `OPENMETEO_API_KEY`.

## License

Apache-2.0 — see [LICENSE](./LICENSE). Open-Meteo data itself is [CC BY 4.0](https://open-meteo.com/en/license); attribute as "Weather data by Open-Meteo.com" if you redistribute the data.
