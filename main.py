from __future__ import annotations

import base64
import os
from mcp.server.fastmcp import FastMCP
from scpi_client import SCPIClient

mcp = FastMCP("SCPI Instrument Control")

# Instrument addresses come from the environment, so this runs against any
# bench without editing source. Override a host with SCPI_ARB_HOST,
# SCPI_DMM_HOST, SCPI_OSC_HOST or SCPI_PSU_HOST, and a port with the matching
# SCPI_<NAME>_PORT. Nearly every instrument listens for raw SCPI on 5025.
DEFAULT_HOSTS = {
    "arb": "arb.local",
    "dmm": "dmm.local",
    "osc": "osc.local",
    "psu": "psu.local",
}


def _device(name: str) -> SCPIClient:
    host = os.environ.get(f"SCPI_{name.upper()}_HOST", DEFAULT_HOSTS[name])
    port = int(os.environ.get(f"SCPI_{name.upper()}_PORT", "5025"))
    return SCPIClient(host, port)


# Device clients
DEVICES = {name: _device(name) for name in DEFAULT_HOSTS}


def _client(device: str) -> SCPIClient:
    if device not in DEVICES:
        raise ValueError(f"Unknown device '{device}'. Use one of: {', '.join(DEVICES)}")
    return DEVICES[device]


# ── Common / IEEE-488 ────────────────────────────────────────────────────────

@mcp.tool()
async def identify(device: str) -> str:
    """Query the identification string of a device.

    Args:
        device: Device key – one of 'arb', 'dmm', 'osc', 'psu'.
    """
    return await _client(device).query("*IDN?")


@mcp.tool()
async def reset(device: str) -> str:
    """Reset a device to factory defaults.

    Args:
        device: Device key – one of 'arb', 'dmm', 'osc', 'psu'.
    """
    await _client(device).send("*RST")
    return f"{device} reset."


@mcp.tool()
async def get_error(device: str) -> str:
    """Read the latest error from the device error queue.

    Args:
        device: Device key – one of 'arb', 'dmm', 'osc', 'psu'.
    """
    return await _client(device).query("SYST:ERR?")


@mcp.tool()
async def send_raw_scpi(device: str, command: str) -> str:
    """Send an arbitrary SCPI command to a device. If the command ends with '?', the response is returned.

    Args:
        device: Device key – one of 'arb', 'dmm', 'osc', 'psu'.
        command: The raw SCPI command string.
    """
    c = _client(device)
    if command.rstrip().endswith("?"):
        return await c.query(command)
    await c.send(command)
    return "OK"


# ── Waveform Generator (SDG 2042X) – device key: arb ─────────────────────────

@mcp.tool()
async def arb_set_waveform(channel: int, waveform: str) -> str:
    """Set the basic waveform type on the waveform generator.

    Args:
        channel: Channel number (1 or 2).
        waveform: Waveform type – SINE, SQUARE, RAMP, PULSE, NOISE, ARB, or DC.
    """
    await _client("arb").send(f"C{channel}:BSWV WVTP,{waveform}")
    return f"C{channel} waveform set to {waveform}."


@mcp.tool()
async def arb_set_frequency(channel: int, frequency: float) -> str:
    """Set the output frequency in Hz on the waveform generator.

    Args:
        channel: Channel number (1 or 2).
        frequency: Frequency in Hz.
    """
    await _client("arb").send(f"C{channel}:BSWV FRQ,{frequency}")
    return f"C{channel} frequency set to {frequency} Hz."


@mcp.tool()
async def arb_set_amplitude(channel: int, amplitude: float) -> str:
    """Set the output amplitude in Vpp on the waveform generator.

    Args:
        channel: Channel number (1 or 2).
        amplitude: Amplitude in Vpp.
    """
    await _client("arb").send(f"C{channel}:BSWV AMP,{amplitude}")
    return f"C{channel} amplitude set to {amplitude} Vpp."


@mcp.tool()
async def arb_set_offset(channel: int, offset: float) -> str:
    """Set the DC offset in volts on the waveform generator.

    Args:
        channel: Channel number (1 or 2).
        offset: Offset in volts.
    """
    await _client("arb").send(f"C{channel}:BSWV OFST,{offset}")
    return f"C{channel} offset set to {offset} V."


@mcp.tool()
async def arb_set_phase(channel: int, phase: float) -> str:
    """Set the phase in degrees on the waveform generator.

    Args:
        channel: Channel number (1 or 2).
        phase: Phase in degrees.
    """
    await _client("arb").send(f"C{channel}:BSWV PHSE,{phase}")
    return f"C{channel} phase set to {phase}°."


@mcp.tool()
async def arb_set_duty_cycle(channel: int, duty: float) -> str:
    """Set the duty cycle (%) for square/pulse waveforms on the waveform generator.

    Args:
        channel: Channel number (1 or 2).
        duty: Duty cycle percentage.
    """
    await _client("arb").send(f"C{channel}:BSWV DUTY,{duty}")
    return f"C{channel} duty cycle set to {duty}%."


@mcp.tool()
async def arb_set_output(channel: int, state: bool) -> str:
    """Enable or disable the output of a waveform generator channel.

    Args:
        channel: Channel number (1 or 2).
        state: True to enable, False to disable.
    """
    await _client("arb").send(f"C{channel}:OUTP {'ON' if state else 'OFF'}")
    return f"C{channel} output {'ON' if state else 'OFF'}."


@mcp.tool()
async def arb_get_output(channel: int) -> str:
    """Query whether a waveform generator channel output is on or off.

    Args:
        channel: Channel number (1 or 2).
    """
    result = await _client("arb").query(f"C{channel}:OUTP?")
    return result


@mcp.tool()
async def arb_set_output_load(channel: int, load: str) -> str:
    """Set the output load impedance on the waveform generator.

    Args:
        channel: Channel number (1 or 2).
        load: 'HZ' for high-impedance or a numeric value in ohms (e.g. '50').
    """
    await _client("arb").send(f"C{channel}:OUTP LOAD,{load}")
    return f"C{channel} load set to {load}."


@mcp.tool()
async def arb_set_polarity(channel: int, polarity: str) -> str:
    """Set the output polarity on the waveform generator.

    Args:
        channel: Channel number (1 or 2).
        polarity: 'NOR' for normal, 'INVT' for inverted.
    """
    await _client("arb").send(f"C{channel}:OUTP PLRT,{polarity}")
    return f"C{channel} polarity set to {polarity}."


@mcp.tool()
async def arb_get_basic_waveform(channel: int) -> str:
    """Query the current basic waveform parameters of a waveform generator channel.

    Args:
        channel: Channel number (1 or 2).
    """
    return await _client("arb").query(f"C{channel}:BSWV?")


@mcp.tool()
async def arb_set_am(channel: int, depth: float, frequency: float) -> str:
    """Enable AM modulation on the waveform generator.

    Args:
        channel: Channel number (1 or 2).
        depth: Modulation depth in percent.
        frequency: Modulation frequency in Hz.
    """
    await _client("arb").send(f"C{channel}:MDWV AM,STATE,ON,MDSP,{depth},FRQ,{frequency}")
    return f"C{channel} AM modulation enabled (depth={depth}%, freq={frequency} Hz)."


@mcp.tool()
async def arb_set_fm(channel: int, deviation: float, frequency: float) -> str:
    """Enable FM modulation on the waveform generator.

    Args:
        channel: Channel number (1 or 2).
        deviation: Frequency deviation in Hz.
        frequency: Modulation frequency in Hz.
    """
    await _client("arb").send(f"C{channel}:MDWV FM,STATE,ON,DEVI,{deviation},FRQ,{frequency}")
    return f"C{channel} FM modulation enabled (deviation={deviation} Hz, freq={frequency} Hz)."


@mcp.tool()
async def arb_set_pm(channel: int, deviation: float, frequency: float) -> str:
    """Enable PM (phase) modulation on the waveform generator.

    Args:
        channel: Channel number (1 or 2).
        deviation: Phase deviation in degrees.
        frequency: Modulation frequency in Hz.
    """
    await _client("arb").send(f"C{channel}:MDWV PM,STATE,ON,DEVI,{deviation},FRQ,{frequency}")
    return f"C{channel} PM modulation enabled (deviation={deviation}°, freq={frequency} Hz)."


@mcp.tool()
async def arb_disable_modulation(channel: int) -> str:
    """Disable all modulation on a waveform generator channel.

    Args:
        channel: Channel number (1 or 2).
    """
    await _client("arb").send(f"C{channel}:MDWV STATE,OFF")
    return f"C{channel} modulation disabled."


@mcp.tool()
async def arb_set_sweep(channel: int, start_freq: float, stop_freq: float, time: float) -> str:
    """Enable frequency sweep on the waveform generator.

    Args:
        channel: Channel number (1 or 2).
        start_freq: Start frequency in Hz.
        stop_freq: Stop frequency in Hz.
        time: Sweep time in seconds.
    """
    await _client("arb").send(f"C{channel}:SWWV STATE,ON,STRF,{start_freq},STPF,{stop_freq},TIME,{time}")
    return f"C{channel} sweep enabled ({start_freq}–{stop_freq} Hz, {time}s)."


@mcp.tool()
async def arb_disable_sweep(channel: int) -> str:
    """Disable frequency sweep on a waveform generator channel.

    Args:
        channel: Channel number (1 or 2).
    """
    await _client("arb").send(f"C{channel}:SWWV STATE,OFF")
    return f"C{channel} sweep disabled."


@mcp.tool()
async def arb_set_burst(channel: int, cycles: int, period: float) -> str:
    """Enable burst mode on the waveform generator.

    Args:
        channel: Channel number (1 or 2).
        cycles: Number of burst cycles.
        period: Burst period in seconds.
    """
    await _client("arb").send(
        f"C{channel}:BTWV STATE,ON,GATE_NCYC,TRSR,MAN,CARR,WVTP,SINE,FRQ,1000,AMP,1,TIME,{period},DLAY,0"
    )
    return f"C{channel} burst enabled ({cycles} cycles, {period}s period)."


@mcp.tool()
async def arb_disable_burst(channel: int) -> str:
    """Disable burst mode on a waveform generator channel.

    Args:
        channel: Channel number (1 or 2).
    """
    await _client("arb").send(f"C{channel}:BTWV STATE,OFF")
    return f"C{channel} burst disabled."


# ── Multimeter (SDM 3055) – device key: dmm ──────────────────────────────────

@mcp.tool()
async def dmm_set_function(function: str) -> str:
    """Set the measurement function on the multimeter.

    Args:
        function: One of VOLT:DC, VOLT:AC, CURR:DC, CURR:AC, RES, FRES, FREQ, PER, CONT, DIOD, CAP.
    """
    await _client("dmm").send(f'FUNC "{function}"')
    return f"DMM function set to {function}."


@mcp.tool()
async def dmm_get_function() -> str:
    """Query the current measurement function on the multimeter."""
    return await _client("dmm").query("FUNC?")


@mcp.tool()
async def dmm_set_range(value: float) -> str:
    """Set the measurement range on the multimeter.

    Args:
        value: Range value (e.g. 10 for 10V range).
    """
    await _client("dmm").send(f"RANG {value}")
    return f"DMM range set to {value}."


@mcp.tool()
async def dmm_set_auto_range(enable: bool) -> str:
    """Enable or disable auto-range on the multimeter.

    Args:
        enable: True to enable, False to disable.
    """
    await _client("dmm").send(f"RANG:AUTO {'ON' if enable else 'OFF'}")
    return f"DMM auto-range {'ON' if enable else 'OFF'}."


@mcp.tool()
async def dmm_get_range() -> str:
    """Query the current measurement range on the multimeter."""
    return await _client("dmm").query("RANG?")


@mcp.tool()
async def dmm_set_resolution(resolution: float) -> str:
    """Set the measurement resolution on the multimeter.

    Args:
        resolution: Resolution value.
    """
    await _client("dmm").send(f"RES {resolution}")
    return f"DMM resolution set to {resolution}."


@mcp.tool()
async def dmm_read() -> str:
    """Take a new measurement reading from the multimeter (triggers and reads)."""
    return await _client("dmm").query("READ?")


@mcp.tool()
async def dmm_fetch() -> str:
    """Fetch the last measurement from the multimeter without triggering a new one."""
    return await _client("dmm").query("FETCH?")


@mcp.tool()
async def dmm_measure(function: str) -> str:
    """Configure and take a single measurement on the multimeter.

    Args:
        function: One of VOLT:DC, VOLT:AC, CURR:DC, CURR:AC, RES, FRES, FREQ, PER.
    """
    return await _client("dmm").query(f"MEAS:{function}?")


@mcp.tool()
async def dmm_enable_statistics() -> str:
    """Enable statistics calculation on the multimeter."""
    await _client("dmm").send("CALC:STAT ON")
    return "DMM statistics enabled."


@mcp.tool()
async def dmm_disable_statistics() -> str:
    """Disable statistics calculation on the multimeter."""
    await _client("dmm").send("CALC:STAT OFF")
    return "DMM statistics disabled."


@mcp.tool()
async def dmm_clear_statistics() -> str:
    """Clear accumulated statistics on the multimeter."""
    await _client("dmm").send("CALC:STAT:CLE")
    return "DMM statistics cleared."


@mcp.tool()
async def dmm_get_statistics() -> str:
    """Query statistics (average, min, max, stddev) from the multimeter."""
    c = _client("dmm")
    avg = await c.query("CALC:AVER?")
    mn = await c.query("CALC:MIN?")
    mx = await c.query("CALC:MAX?")
    sd = await c.query("CALC:SDEV?")
    return f"Average: {avg}, Min: {mn}, Max: {mx}, StdDev: {sd}"


@mcp.tool()
async def dmm_set_trigger_source(source: str) -> str:
    """Set the trigger source on the multimeter.

    Args:
        source: One of IMM, BUS, EXT.
    """
    await _client("dmm").send(f"TRIG:SOUR {source}")
    return f"DMM trigger source set to {source}."


@mcp.tool()
async def dmm_trigger() -> str:
    """Send a software trigger to the multimeter."""
    await _client("dmm").send("*TRG")
    return "DMM triggered."


@mcp.tool()
async def dmm_set_nplc(nplc: float) -> str:
    """Set the integration time in number of power line cycles on the multimeter.

    Args:
        nplc: NPLC value (e.g. 0.02, 0.2, 1, 10, 100).
    """
    await _client("dmm").send(f"VOLT:DC:NPLC {nplc}")
    return f"DMM NPLC set to {nplc}."


# ── Oscilloscope (SDS 1202X-E) – device key: osc ─────────────────────────────

@mcp.tool()
async def osc_set_channel_state(channel: int, state: bool) -> str:
    """Enable or disable a channel trace on the oscilloscope.

    Args:
        channel: Channel number (1 or 2).
        state: True to enable, False to disable.
    """
    await _client("osc").send(f"C{channel}:TRA {'ON' if state else 'OFF'}")
    return f"C{channel} trace {'ON' if state else 'OFF'}."


@mcp.tool()
async def osc_set_channel_scale(channel: int, scale: float) -> str:
    """Set the vertical scale (V/div) of an oscilloscope channel.

    Args:
        channel: Channel number (1 or 2).
        scale: Volts per division.
    """
    await _client("osc").send(f"C{channel}:VDIV {scale}")
    return f"C{channel} scale set to {scale} V/div."


@mcp.tool()
async def osc_set_channel_offset(channel: int, offset: float) -> str:
    """Set the vertical offset of an oscilloscope channel.

    Args:
        channel: Channel number (1 or 2).
        offset: Offset in volts.
    """
    await _client("osc").send(f"C{channel}:OFST {offset}")
    return f"C{channel} offset set to {offset} V."


@mcp.tool()
async def osc_set_channel_coupling(channel: int, coupling: str) -> str:
    """Set the coupling mode of an oscilloscope channel.

    Args:
        channel: Channel number (1 or 2).
        coupling: One of AC, DC, GND.
    """
    await _client("osc").send(f"C{channel}:CPL {coupling}")
    return f"C{channel} coupling set to {coupling}."


@mcp.tool()
async def osc_set_probe_attenuation(channel: int, attenuation: float) -> str:
    """Set the probe attenuation factor on an oscilloscope channel.

    Args:
        channel: Channel number (1 or 2).
        attenuation: Attenuation factor (e.g. 1, 10, 100).
    """
    await _client("osc").send(f"C{channel}:ATTN {attenuation}")
    return f"C{channel} probe attenuation set to {attenuation}x."


@mcp.tool()
async def osc_set_timebase(scale: float) -> str:
    """Set the horizontal timebase (s/div) on the oscilloscope.

    Args:
        scale: Time per division in seconds.
    """
    await _client("osc").send(f"TDIV {scale}")
    return f"Timebase set to {scale} s/div."


@mcp.tool()
async def osc_get_timebase() -> str:
    """Query the current timebase setting on the oscilloscope."""
    return await _client("osc").query("TDIV?")


@mcp.tool()
async def osc_set_trigger_mode(mode: str) -> str:
    """Set the trigger mode on the oscilloscope.

    Args:
        mode: One of AUTO, NORM, SINGLE, STOP.
    """
    await _client("osc").send(f"TRMD {mode}")
    return f"Trigger mode set to {mode}."


@mcp.tool()
async def osc_set_trigger_source(channel: int) -> str:
    """Set the trigger source channel on the oscilloscope.

    Args:
        channel: Channel number (1 or 2).
    """
    await _client("osc").send(f"TRSE EDGE,SR,C{channel}")
    return f"Trigger source set to C{channel}."


@mcp.tool()
async def osc_set_trigger_level(level: float) -> str:
    """Set the trigger level in volts on the oscilloscope.

    Args:
        level: Trigger level in volts.
    """
    await _client("osc").send(f"TRLV {level}")
    return f"Trigger level set to {level} V."


@mcp.tool()
async def osc_set_trigger_slope(slope: str) -> str:
    """Set the trigger slope on the oscilloscope.

    Args:
        slope: 'POS' for rising edge, 'NEG' for falling edge.
    """
    await _client("osc").send(f"TRSL {slope}")
    return f"Trigger slope set to {slope}."


@mcp.tool()
async def osc_force_trigger() -> str:
    """Force a trigger event on the oscilloscope."""
    await _client("osc").send("FRTR")
    return "Trigger forced."


@mcp.tool()
async def osc_measure(channel: int, parameter: str) -> str:
    """Measure a waveform parameter on the oscilloscope.

    Args:
        channel: Channel number (1 or 2).
        parameter: One of PKPK, MAX, MIN, AMPL, TOP, BASE, MEAN, RMS, FREQ, PER, RISE, FALL, DUTY, WID, NWID, DELAY, OVSP, OVSH.
    """
    return await _client("osc").query(f"C{channel}:PAVA? {parameter}")


@mcp.tool()
async def osc_auto_setup() -> str:
    """Run auto-setup on the oscilloscope."""
    await _client("osc").send("ASET")
    return "Auto-setup executed."


@mcp.tool()
async def osc_run() -> str:
    """Start acquisition (set trigger mode to AUTO) on the oscilloscope."""
    await _client("osc").send("TRMD AUTO")
    return "Oscilloscope running."


@mcp.tool()
async def osc_stop() -> str:
    """Stop acquisition on the oscilloscope."""
    await _client("osc").send("TRMD STOP")
    return "Oscilloscope stopped."


@mcp.tool()
async def osc_single() -> str:
    """Set the oscilloscope to single-trigger mode."""
    await _client("osc").send("TRMD SINGLE")
    return "Oscilloscope set to single trigger."


@mcp.tool()
async def osc_screenshot() -> str:
    """Capture a screenshot from the oscilloscope. Returns base64-encoded PNG data."""
    c = _client("osc")
    await c.send("HCSU DEV,PNG")
    await c.send("HCSU AREA,GRIDAREA")
    # SCDP on the SDS1202X-E returns raw image bytes with no IEEE 488.2 length
    # header and no line terminator, so read until the socket goes idle.
    raw = await c.query_raw("SCDP")
    return base64.b64encode(raw).decode()


@mcp.tool()
async def osc_get_channel_info(channel: int) -> str:
    """Query full channel setup info from the oscilloscope.

    Args:
        channel: Channel number (1 or 2).
    """
    return await _client("osc").query(f"C{channel}:VDIV?")


@mcp.tool()
async def osc_set_memory_size(size: str) -> str:
    """Set the acquisition memory depth on the oscilloscope.

    Args:
        size: Memory size, e.g. '7K', '70K', '700K', '7M', '14M'.
    """
    await _client("osc").send(f"MSIZ {size}")
    return f"Memory size set to {size}."


@mcp.tool()
async def osc_set_acquire_mode(mode: str) -> str:
    """Set the acquisition mode on the oscilloscope.

    Args:
        mode: One of SAMPLING, PEAK_DETECT, AVERAGE.
    """
    await _client("osc").send(f"ACQW {mode}")
    return f"Acquire mode set to {mode}."


@mcp.tool()
async def osc_set_average_count(count: int) -> str:
    """Set the number of averages when in average acquisition mode.

    Args:
        count: Number of averages (power of 2, e.g. 4, 16, 64, 256).
    """
    await _client("osc").send(f"AVGA {count}")
    return f"Average count set to {count}."


# ── Power Supply (SPD3303X-E) – device key: psu ──────────────────────────────

@mcp.tool()
async def psu_set_voltage(channel: int, voltage: float) -> str:
    """Set the output voltage on a power supply channel.

    Args:
        channel: Channel number (1, 2, or 3).
        voltage: Voltage in volts.
    """
    await _client("psu").send(f"CH{channel}:VOLT {voltage}")
    return f"CH{channel} voltage set to {voltage} V."


@mcp.tool()
async def psu_set_current(channel: int, current: float) -> str:
    """Set the output current limit on a power supply channel.

    Args:
        channel: Channel number (1, 2, or 3).
        current: Current in amps.
    """
    await _client("psu").send(f"CH{channel}:CURR {current}")
    return f"CH{channel} current set to {current} A."


@mcp.tool()
async def psu_get_voltage(channel: int) -> str:
    """Query the set voltage on a power supply channel.

    Args:
        channel: Channel number (1, 2, or 3).
    """
    return await _client("psu").query(f"CH{channel}:VOLT?")


@mcp.tool()
async def psu_get_current(channel: int) -> str:
    """Query the set current limit on a power supply channel.

    Args:
        channel: Channel number (1, 2, or 3).
    """
    return await _client("psu").query(f"CH{channel}:CURR?")


@mcp.tool()
async def psu_measure_voltage(channel: int) -> str:
    """Measure the actual output voltage on a power supply channel.

    Args:
        channel: Channel number (1, 2, or 3).
    """
    return await _client("psu").query(f"MEAS:VOLT? CH{channel}")


@mcp.tool()
async def psu_measure_current(channel: int) -> str:
    """Measure the actual output current on a power supply channel.

    Args:
        channel: Channel number (1, 2, or 3).
    """
    return await _client("psu").query(f"MEAS:CURR? CH{channel}")


@mcp.tool()
async def psu_measure_power(channel: int) -> str:
    """Measure the actual output power on a power supply channel.

    Args:
        channel: Channel number (1, 2, or 3).
    """
    return await _client("psu").query(f"MEAS:POWE? CH{channel}")


@mcp.tool()
async def psu_set_output(channel: int, state: bool) -> str:
    """Enable or disable the output of a power supply channel.

    Args:
        channel: Channel number (1, 2, or 3).
        state: True to enable, False to disable.
    """
    await _client("psu").send(f"OUTP CH{channel},{'ON' if state else 'OFF'}")
    return f"CH{channel} output {'ON' if state else 'OFF'}."


@mcp.tool()
async def psu_get_output(channel: int) -> str:
    """Query whether a power supply channel output is on or off.

    Args:
        channel: Channel number (1, 2, or 3).
    """
    return await _client("psu").query(f"OUTP? CH{channel}")


@mcp.tool()
async def psu_set_ovp(channel: int, voltage: float) -> str:
    """Set the over-voltage protection threshold on a power supply channel.

    Args:
        channel: Channel number (1 or 2).
        voltage: OVP threshold in volts.
    """
    await _client("psu").send(f"CH{channel}:VOLT:PROT {voltage}")
    return f"CH{channel} OVP set to {voltage} V."


@mcp.tool()
async def psu_set_ocp(channel: int, current: float) -> str:
    """Set the over-current protection threshold on a power supply channel.

    Args:
        channel: Channel number (1 or 2).
        current: OCP threshold in amps.
    """
    await _client("psu").send(f"CH{channel}:CURR:PROT {current}")
    return f"CH{channel} OCP set to {current} A."


@mcp.tool()
async def psu_recall(preset: int) -> str:
    """Recall a saved preset on the power supply.

    Args:
        preset: Preset number (1–5).
    """
    await _client("psu").send(f"*RCL {preset}")
    return f"Preset {preset} recalled."


@mcp.tool()
async def psu_save(preset: int) -> str:
    """Save the current settings to a preset on the power supply.

    Args:
        preset: Preset number (1–5).
    """
    await _client("psu").send(f"*SAV {preset}")
    return f"Settings saved to preset {preset}."


@mcp.tool()
async def psu_set_mode(mode: str) -> str:
    """Set the channel tracking mode on the power supply.

    Args:
        mode: One of INDEPENDENT, SERIES, PARALLEL.
    """
    mode_map = {"INDEPENDENT": "0", "SERIES": "1", "PARALLEL": "2"}
    code = mode_map.get(mode.upper(), "0")
    await _client("psu").send(f"OUTP:TRACK {code}")
    return f"PSU mode set to {mode}."


@mcp.tool()
async def psu_get_status() -> str:
    """Query the system status register of the power supply (channel modes, output states)."""
    return await _client("psu").query("SYST:STAT?")


if __name__ == "__main__":
    mcp.run(transport="stdio")
