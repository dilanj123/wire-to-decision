import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tb" / "functional_mvp"))
from test_functional_mvp import beats  # noqa: E402


def signed49(signal):
    value = int(signal.value)
    return value - (1 << 49) if value & (1 << 48) else value


def load_replay(path):
    config = {}
    frames = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line == "WIRE_REPLAY_V1":
            continue
        if line.startswith("CONFIG "):
            for field in line.split()[1:]:
                key, value = field.split("=", 1)
                config[key] = value
        elif line.startswith("FRAME "):
            frames.append(bytes.fromhex(line.split(maxsplit=1)[1]))
        else:
            raise AssertionError(f"unsupported canonical replay line: {line}")
    assert config and frames
    return config, frames


@cocotb.test()
async def export_actual_functional_top_decisions(dut):
    replay_path = ROOT / "tools" / "cpp" / "replays" / "canonical.w2d"
    config, frames = load_replay(replay_path)
    dut._log.info("CPP_REPLAY source=%s frames=%d", replay_path, len(frames))

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    pins = {
        "rst": 1, "rearm": 0,
        "cfg_destination_ipv4": int(config["destination_ip"], 0),
        "cfg_destination_udp_port": int(config["destination_port"], 0),
        "cfg_active_session": int.from_bytes(bytes.fromhex(config["session"]), "big"),
        "cfg_expected_sequence": int(config["expected_sequence"], 0),
        "cfg_tracked_stock_locate": int(config["tracked_locate"], 0),
        "cfg_symbol_check_enable": int(config["symbol_check"]),
        "cfg_expected_stock_symbol": int.from_bytes(bytes.fromhex(config["symbol"]), "big"),
        "cfg_decision_threshold": int(config["threshold"], 0),
        "cfg_initial_budget": int(config["budget"], 0),
        "decision_enable": int(config["enable"]),
        "rx_data": 0, "rx_keep": 0, "rx_valid": 0, "rx_last": 0,
        "decision_ready": 1, "error_ready": 1, "debug_reference": 0,
    }
    for name, value in pins.items():
        getattr(dut, name).value = value
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0

    stream = []
    for frame_index, packet in enumerate(frames):
        stream.extend((frame_index, beat) for beat in beats(packet))

    parser = dut.parser_book.parser
    message_valid = parser.msg_valid
    message_ready = parser.msg_ready
    message_last = parser.msg_last
    message_sequence = parser.message_sequence
    metadata_valid = parser.message_valid
    metadata_ready = parser.message_ready

    frame_first_cycle = {}
    message_first_cycle = {}
    message_last_cycle = {}
    event_cycle = {}
    decisions = []
    latency_records = []
    active_message_sequence = None
    index = 0
    cycle = 0
    for _ in range(10000):
        await FallingEdge(dut.clk)
        if index < len(stream):
            _, (data, keep, last) = stream[index]
            dut.rx_data.value = data
            dut.rx_keep.value = keep
            dut.rx_last.value = last
            dut.rx_valid.value = 1
        await Timer(1, unit="ns")

        rx_fire = index < len(stream) and int(dut.rx_valid.value) and int(dut.rx_ready.value)
        if rx_fire:
            frame_index = stream[index][0]
            frame_first_cycle.setdefault(frame_index, cycle)
        if int(metadata_valid.value) and int(metadata_ready.value):
            active_message_sequence = int(message_sequence.value)
        if int(message_valid.value) and int(message_ready.value):
            assert active_message_sequence is not None
            message_first_cycle.setdefault(active_message_sequence, cycle)
            if int(message_last.value):
                message_last_cycle[active_message_sequence] = cycle
        if int(dut.event_valid_observed.value) and int(dut.event_ready_observed.value):
            event_cycle[int(dut.event_mold_sequence_observed.value)] = cycle

        if int(dut.decision_valid.value):
            seq = int(dut.decision_mold_sequence.value)
            record = {
                "cycle": cycle,
                "action": "SELL" if int(dut.decision_action.value) else "BUY",
                "mold_sequence": seq,
                "itch_timestamp": int(dut.decision_itch_timestamp.value),
                "imbalance": signed49(dut.decision_signed_imbalance),
            }
            decisions.append(record)
            frame_index = seq - int(config["expected_sequence"], 0)
            # The canonical replay has one normal Mold message in each of its
            # first three frames and one zero-count heartbeat.
            frame_index = min(frame_index, len(frames) - 1)
            assert seq in message_first_cycle and seq in message_last_cycle and seq in event_cycle
            latency_records.append({
                "cycle": cycle,
                "l1": event_cycle[seq] - message_first_cycle[seq],
                "l2": cycle - message_last_cycle[seq],
                "l3": cycle - frame_first_cycle[frame_index],
            })

        await RisingEdge(dut.clk)
        if rx_fire:
            index += 1
            dut.rx_valid.value = 0
        cycle += 1
        if index == len(stream) and len(decisions) == 2:
            # Allow the final sequential state updates to settle.
            for _ in range(8):
                await RisingEdge(dut.clk)
                cycle += 1
            break
    assert index == len(stream), f"accepted only {index}/{len(stream)} beats"
    assert [(d["action"], d["mold_sequence"], d["itch_timestamp"], d["imbalance"])
            for d in decisions] == [
                ("BUY", int(config["expected_sequence"], 0), 0x010203040501, 10),
                ("SELL", int(config["expected_sequence"], 0) + 1, 0x010203040502, -10),
            ]
    assert int(dut.bid_total.value) == 10
    assert int(dut.ask_total.value) == 20
    assert int(dut.current_expected_sequence.value) == int(config["expected_sequence"], 0) + 3
    assert int(dut.parser_recovery_required.value) == 0
    assert int(dut.book_recovery_required.value) == 0

    out_dir = ROOT / "results" / "raw" / "cpp"
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "rtl_decisions.log").open("w") as output:
        output.write("WIRE_RTL_LOG_V1\n")
        for decision in decisions:
            output.write("DECISION cycle={cycle} action={action} mold_sequence={mold_sequence} "
                         "itch_timestamp={itch_timestamp} imbalance={imbalance}\n".format(**decision))
        for latency in latency_records:
            output.write("LATENCY cycle={cycle} l1={l1} l2={l2} l3={l3}\n".format(**latency))
        output.write(
            f"STATE bid_total={int(dut.bid_total.value)} ask_total={int(dut.ask_total.value)} "
            f"expected_sequence={int(dut.current_expected_sequence.value)} quarantined=0\n"
        )
    dut._log.info("CPP_REPLAY_RESULT frames=%d beats=%d cycles=%d decisions=%s latency=%s",
                  len(frames), len(stream), cycle, decisions, latency_records)
