# SCPI MCP

An MCP server that puts benchtop test equipment within reach of an agentic
coding harness. Point Claude Code, Codex or any other MCP client at it and ask
it to go investigate a circuit.

It exposes four instruments as 76 typed tools, plus a raw SCPI passthrough for
everything the wrappers do not cover:

| Device key | Instrument |
| --- | --- |
| `arb` | Arbitrary waveform generator |
| `dmm` | Multimeter |
| `osc` | Oscilloscope |
| `psu` | Power supply |

Anything that speaks [SCPI](https://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments)
over a socket should work. SCPI is a text protocol standardized in 1990, which
turns out to suit this well: instruments that already take commands as strings
do not need much of an adapter to take them from a model.

## Why it is useful

The oscilloscope can hand back screenshots. That matters more than it sounds,
because a lot of what a scope tells you is a shape rather than a number, and a
model that can look at the trace reasons about it the way a person would
instead of working from whichever measurements someone thought to request in
advance.

The useful range runs from "set a rising edge trigger at 2.5 volts on channel
2", which just saves a menu dive, up to handing over a misbehaving circuit and
letting the model drive all four instruments to work out why.

## Requirements

- Python 3.10 or newer
- Instruments reachable over the network, listening for raw SCPI (port 5025 on
  nearly everything)

## Install

```sh
git clone https://github.com/colingimenez/scpi-mcp.git
cd scpi-mcp
uv sync
```

## Configuration

Instrument addresses come from the environment, so nothing needs editing in
source. Set only the ones you have.

| Variable | Default |
| --- | --- |
| `SCPI_ARB_HOST` | `arb.local` |
| `SCPI_DMM_HOST` | `dmm.local` |
| `SCPI_OSC_HOST` | `osc.local` |
| `SCPI_PSU_HOST` | `psu.local` |
| `SCPI_<NAME>_PORT` | `5025` |

## Use it from an MCP client

```json
{
  "mcpServers": {
    "scpi": {
      "command": "uv",
      "args": ["--directory", "/path/to/scpi-mcp", "run", "main.py"],
      "env": {
        "SCPI_OSC_HOST": "192.0.2.10",
        "SCPI_PSU_HOST": "192.0.2.11"
      }
    }
  }
}
```

## A note on safety

Raw SCPI has no authentication of any kind. Anything that can reach port 5025
on an instrument can drive it, and this server does nothing to change that. Put
your bench on a network you trust.

The tools will also happily turn a power supply on, change its voltage, and
reset an instrument to factory defaults, because that is the point. Be aware
that a model driving this is driving real hardware with real things wired to
it.

## Known specifics

Oscilloscope screenshot capture is written against the Siglent SDS1202X-E,
which streams a raw image with no length header and no terminator. Other scopes
implement this differently and may need their own path.
