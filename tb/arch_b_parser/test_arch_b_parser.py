import random
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model" / "python"))
from wire_to_decision.oracle import ReferenceOracle
from wire_to_decision.types import ModelConfig

DEST_IP = 0xC6336407
DEST_PORT = 0x1234
LOC = 0x2345
SESSION = b"W2DTEST001"
BASE_SEQ = 0x1020304050607080
SYMBOL = b"ALPH    "


def put(buf, off, n, value):
    buf[off:off+n] = value.to_bytes(n, "big")


def checksum(data):
    if len(data) & 1:
        data += b"\0"
    total = sum(int.from_bytes(data[i:i+2], "big") for i in range(0, len(data), 2))
    while total >> 16:
        total = (total & 0xffff) + (total >> 16)
    return (~total) & 0xffff


def itch(kind, ref, qty=10, price=0x12345678, side=b"B", locate=LOC, salt=0):
    sizes = {"A":36,"F":40,"E":31,"C":36,"X":23,"D":19,"U":35,"P":44}
    x = bytearray(sizes[kind]); x[0] = ord(kind)
    if len(x) >= 11:
        put(x,1,2,locate); put(x,3,2,0xA100+salt); put(x,5,6,0x010203040500+salt)
    if kind in "AF":
        put(x,11,8,ref); x[19]=side[0]; put(x,20,4,qty); x[24:32]=SYMBOL; put(x,32,4,price)
        if kind == "F": x[36:40]=b"MPID"
    elif kind in "ECX":
        put(x,11,8,ref); put(x,19,4,qty)
        if kind == "C": x[23]=1; put(x,24,4,0xDEADBEEF); x[28:36]=b"XYZ12345"
    elif kind == "D": put(x,11,8,ref)
    elif kind == "U":
        put(x,11,8,ref); put(x,19,8,0x8877665544332211+salt); put(x,27,4,qty); put(x,31,4,price)
    return bytes(x)


def mold(msgs, seq):
    body = b"".join(len(m).to_bytes(2,"big")+m for m in msgs)
    return SESSION + seq.to_bytes(8,"big") + len(msgs).to_bytes(2,"big") + body


def mold_raw(count, body, seq=BASE_SEQ, session=SESSION):
    return session + seq.to_bytes(8,"big") + count.to_bytes(2,"big") + body


def frame(payload, *, dport=DEST_PORT, dip=DEST_IP, udp_checksum=0, ether_type=0x0800):
    udp = bytearray(8); put(udp,0,2,0xBEEF); put(udp,2,2,dport); put(udp,4,2,8+len(payload)); put(udp,6,2,udp_checksum)
    ip = bytearray(20); ip[0]=0x45; put(ip,2,2,20+len(udp)+len(payload)); ip[8]=64; ip[9]=17
    put(ip,16,4,dip); put(ip,10,2,checksum(bytes(ip)))
    return bytes.fromhex("0201020304050A0B0C0D0E0F")+ether_type.to_bytes(2,"big")+bytes(ip)+bytes(udp)+payload


def beats(data):
    out=[]
    for off in range(0,len(data),8):
        p=data[off:off+8]
        out.append((sum(v << (8*i) for i,v in enumerate(p)), (1<<len(p))-1, int(off+len(p)==len(data))))
    return out


def unpack_event(v):
    fields=[1,1,1,1,1,1,32,32,64,64,16,48,64,8,3]
    vals=[]
    for width in fields:
        vals.append(v & ((1<<width)-1)); v >>= width
    return tuple(reversed(vals))


def oracle_tuple(event):
    kinds={"ADD":0,"EXECUTE":1,"EXECUTE_WITH_PRICE":2,"CANCEL":3,"DELETE":4,"REPLACE":5}
    valid=event.field_valid
    return (kinds[event.kind.value], ord(event.source_type.value), event.mold_sequence,
        event.itch_timestamp, event.stock_locate, event.old_order_reference or 0,
        event.new_order_reference or 0, event.quantity or 0, event.price or 0,
        int(event.side is not None and event.side.value=="S"), int(valid.old_order_reference),
        int(valid.new_order_reference), int(valid.quantity), int(valid.price), int(valid.side))


def oracle_config():
    return ModelConfig(DEST_IP,DEST_PORT,LOC,True,SYMBOL,SESSION,BASE_SEQ,10,20,True)


async def reset(d):
    d.rst.value=1; d.rearm.value=0; d.rx_valid.value=0; d.rx_data.value=0; d.rx_keep.value=0; d.rx_last.value=0
    d.cfg_destination_ipv4.value=DEST_IP; d.cfg_destination_udp_port.value=DEST_PORT
    d.cfg_active_session.value=int.from_bytes(SESSION,"big"); d.cfg_expected_sequence.value=BASE_SEQ
    d.cfg_tracked_stock_locate.value=LOC; d.cfg_symbol_check_enable.value=1
    d.cfg_expected_stock_symbol.value=int.from_bytes(SYMBOL,"big")
    d.a_event_ready.value=1; d.b_event_ready.value=1
    await RisingEdge(d.clk); await FallingEdge(d.clk); d.rst.value=0


async def send(d, data, max_cycles=10000, stall_events=False):
    seq=beats(data); idx=0; held=None; aevents=[]; bevents=[]
    last_a_stall=None; last_b_stall=None
    stall_state=0; stall_left=0
    for cycle in range(max_cycles):
        await FallingEdge(d.clk)
        if held is None and idx<len(seq):
            held=seq[idx]; d.rx_data.value,d.rx_keep.value,d.rx_last.value=held; d.rx_valid.value=1
        ready = int(not stall_events or stall_state == 2)
        d.a_event_ready.value=ready; d.b_event_ready.value=ready
        await Timer(1,unit="ns")
        av=(int(d.a_event_valid.value),int(d.a_event.value))
        bv=(int(d.b_event_valid.value),int(d.b_event.value))
        if last_a_stall is not None: assert av == last_a_stall and av[0]
        if last_b_stall is not None: assert bv == last_b_stall and bv[0]
        if int(d.a_event_valid.value) and int(d.a_event_ready.value): aevents.append(unpack_event(int(d.a_event.value)))
        if int(d.b_event_valid.value) and int(d.b_event_ready.value):
            bevents.append(unpack_event(int(d.b_event.value)))
        last_a_stall=av if av[0] and not ready else None
        last_b_stall=bv if bv[0] and not ready else None
        fire=int(d.rx_valid.value) and int(d.rx_ready.value)
        await RisingEdge(d.clk)
        a_fire=av[0] and ready; b_fire=bv[0] and ready
        if stall_events:
            if stall_state == 0 and av[0] and bv[0]: stall_state=1; stall_left=3
            elif stall_state == 1:
                stall_left-=1
                if stall_left==0: stall_state=2
            elif stall_state == 2 and a_fire and b_fire: stall_state=0
        if fire:
            idx+=1; held=None; d.rx_valid.value=0
        if idx==len(seq): break
    else: raise AssertionError(f"input timeout {idx}/{len(seq)} ready={int(d.rx_ready.value)} "
        f"Arec={int(d.a_recovery.value)} Brec={int(d.b_recovery.value)} "
        f"Bstage={int(d.b.recovery_stage_q.value)} iprem={int(d.b.ip_payload_remaining_q.value)} "
        f"Bseq={int(d.b.expected_sequence_q.value):x} "
        f"iplen={int(d.b.ip_total_q.value)} udpidx={int(d.b.udp_index_q.value)} "
        f"Bstate={int(d.b.state_q.value)} Bbeat={int(d.b.beat_active_q.value)} "
        f"Bcount={int(d.b.ingress.count_q.value)}")
    d.rx_valid.value=0
    for cycle in range(3000):
        await FallingEdge(d.clk)
        ready = int(not stall_events or stall_state == 2)
        d.a_event_ready.value=ready; d.b_event_ready.value=ready
        await Timer(1,unit="ns")
        av=(int(d.a_event_valid.value),int(d.a_event.value))
        bv=(int(d.b_event_valid.value),int(d.b_event.value))
        if last_a_stall is not None: assert av == last_a_stall and av[0]
        if last_b_stall is not None: assert bv == last_b_stall and bv[0]
        if int(d.a_event_valid.value) and int(d.a_event_ready.value): aevents.append(unpack_event(int(d.a_event.value)))
        if int(d.b_event_valid.value) and int(d.b_event_ready.value):
            bevents.append(unpack_event(int(d.b_event.value)))
        last_a_stall=av if av[0] and not ready else None
        last_b_stall=bv if bv[0] and not ready else None
        await RisingEdge(d.clk)
        a_fire=av[0] and ready; b_fire=bv[0] and ready
        if stall_events:
            if stall_state == 0 and av[0] and bv[0]: stall_state=1; stall_left=3
            elif stall_state == 1:
                stall_left-=1
                if stall_left==0: stall_state=2
            elif stall_state == 2 and a_fire and b_fire: stall_state=0
    assert aevents == bevents, (f"A/B mismatch Arec={int(d.a_recovery.value)} "
        f"Brec={int(d.b_recovery.value)} Bseq={int(d.b_expected_sequence.value):x} "
        f"state={int(d.b.state_q.value)} rem={int(d.b.ip_payload_remaining_q.value)} "
        f"msgrem={int(d.b.msg_remaining_q.value)} itchrem={int(d.b.itch_remaining_q.value)} "
        f"msglen={int(d.b.msg_length_q.value)} idx={int(d.b.msg_index_q.value)} "
        f"eventv={int(d.b.event_valid_q.value)} type={int(d.b.msg_q[0].value)} "
        f"loc={int(d.b.msg_q[1].value):02x}{int(d.b.msg_q[2].value):02x} "
        f"A={aevents}\nB={bevents}")
    return bevents


@cocotb.test()
async def supported_messages_and_lane_boundaries(d):
    cocotb.start_soon(Clock(d.clk,10,unit="ns").start())
    await reset(d)
    messages=[itch("A",0x1122334455667788,salt=0), itch("F",0x8877665544332211,salt=1),
              itch("E",0x1122334455667788,qty=2,salt=2), itch("C",0x1122334455667788,qty=1,salt=3),
              itch("X",0x1122334455667788,qty=1,salt=4), itch("D",0x1122334455667788,salt=5),
              itch("U",0x8877665544332211,qty=7,salt=6), itch("P",0,salt=7)]
    got=await send(d,frame(mold(messages,BASE_SEQ)))
    assert [x[1] for x in got] == list(b"AFECXDU")
    assert [x[2] for x in got] == [BASE_SEQ+i for i in range(7)]
    assert [x[4] for x in got] == [LOC]*7
    assert got[0][7:15] == (10,0x12345678,0,0,1,1,1,1)
    assert got[2][0] == 1 and got[3][0] == 2 and got[3][13] == 0
    assert got[5][0] == 4 and got[6][0] == 5
    assert int(d.b_expected_sequence.value) == BASE_SEQ+len(messages)
    assert int(d.a_recovery.value)==0 and int(d.b_recovery.value)==0
    oracle=ReferenceOracle(oracle_config()).process_frame(frame(mold(messages,BASE_SEQ)))
    assert oracle.accepted and not oracle.quarantined
    expected=[oracle_tuple(row.decode_result.event) for row in oracle.messages
              if row.decode_result.event is not None]
    assert got==expected


@cocotb.test()
async def filters_partial_keep_and_rearm(d):
    cocotb.start_soon(Clock(d.clk,10,unit="ns").start())
    await reset(d)
    m=itch("A",0x123456789ABCDEF0,salt=1)
    assert await send(d,frame(mold([m],BASE_SEQ)))
    assert await send(d,frame(mold([itch("A",2,locate=LOC+1)],BASE_SEQ+1))) == []
    assert await send(d,frame(mold([itch("P",0)],BASE_SEQ+2))) == []
    # Wrong destination is a nonfatal frame filter.
    assert await send(d,frame(mold([itch("A",3)],BASE_SEQ+3),dport=0x3412)) == []
    assert int(d.b_recovery.value)==0
    await reset(d)
    bad=bytearray(itch("A",4)); bad[19]=ord("Q")
    # The semantic failure is detected after the complete message boundary.
    await send(d,frame(mold([bytes(bad),itch("A",5)],BASE_SEQ)))
    assert int(d.b_recovery.value)==1
    d.rearm.value=1; await RisingEdge(d.clk); await FallingEdge(d.clk); d.rearm.value=0
    await Timer(1,unit="ns")
    assert int(d.b_recovery.value)==0


@cocotb.test()
async def deterministic_lane_vectors(d):
    cocotb.start_soon(Clock(d.clk,10,unit="ns").start())
    for seed in (1,7,19,42,97):
        await reset(d)
        rng=random.Random(seed)
        msgs=[itch("A",rng.getrandbits(64),salt=i) for i in range(3)]
        got=await send(d,frame(mold(msgs,BASE_SEQ)))
        assert len(got)==3 and [x[2] for x in got]==[BASE_SEQ+i for i in range(3)]


@cocotb.test()
async def heartbeat_checksum_and_outer_filters(d):
    cocotb.start_soon(Clock(d.clk,10,unit="ns").start())
    await reset(d)
    assert await send(d,frame(mold([],BASE_SEQ))) == []
    assert int(d.b_expected_sequence.value)==BASE_SEQ
    assert await send(d,frame(mold([itch("A",0x99)],BASE_SEQ)))
    assert await send(d,frame(mold([itch("A",0x100)],BASE_SEQ+1),udp_checksum=1)) == []
    assert int(d.b_recovery.value)==0
    assert int(d.b_expected_sequence.value)==BASE_SEQ+1
    assert await send(d,frame(mold([itch("A",0x101)],BASE_SEQ+2),ether_type=0x86DD)) == []
    assert int(d.b_recovery.value)==0
    assert await send(d,frame(mold([itch("A",0x102)],BASE_SEQ+1)))


@cocotb.test()
async def structural_truncation_and_rearm(d):
    cocotb.start_soon(Clock(d.clk,10,unit="ns").start())
    await reset(d)
    prefix=itch("A",0x123456789ABCDEF0)
    raw=(len(prefix).to_bytes(2,"big")+prefix+bytes.fromhex("0005aabb"))
    got=await send(d,frame(mold_raw(2,raw,BASE_SEQ)))
    assert len(got)==1 and got[0][1]==ord("A")
    assert int(d.b_recovery.value)==1
    assert int(d.b_expected_sequence.value)==BASE_SEQ
    # Explicit rearm reloads the same known epoch and permits a fresh packet.
    d.rearm.value=1; await RisingEdge(d.clk); await FallingEdge(d.clk); d.rearm.value=0
    assert int(d.b_recovery.value)==0
    assert await send(d,frame(mold([itch("A",7)],BASE_SEQ)))


@cocotb.test()
async def mold_control_and_outer_truncation(d):
    cocotb.start_soon(Clock(d.clk,10,unit="ns").start())
    await reset(d)
    assert await send(d,frame(mold([],BASE_SEQ))) == []  # exact heartbeat
    assert int(d.b_expected_sequence.value)==BASE_SEQ
    assert await send(d,frame(mold_raw(0,b"\xaa\xbb",BASE_SEQ))) == []
    assert int(d.b_recovery.value)==1 and int(d.b_expected_sequence.value)==BASE_SEQ
    d.rearm.value=1; await RisingEdge(d.clk); await FallingEdge(d.clk); d.rearm.value=0
    assert await send(d,frame(mold_raw(0xffff,b"",BASE_SEQ))) == []  # exact EOS
    assert int(d.b_recovery.value)==1 and int(d.b_expected_sequence.value)==BASE_SEQ
    d.rearm.value=1; await RisingEdge(d.clk); await FallingEdge(d.clk); d.rearm.value=0
    assert await send(d,frame(mold([itch("A",0x77)],BASE_SEQ+1))) == []
    assert int(d.b_recovery.value)==1 and int(d.b_expected_sequence.value)==BASE_SEQ
    d.rearm.value=1; await RisingEdge(d.clk); await FallingEdge(d.clk); d.rearm.value=0
    truncated=frame(mold([itch("A",0x88)],BASE_SEQ))[:-4]
    assert await send(d,truncated) == []
    assert int(d.b_recovery.value)==1


@cocotb.test()
async def header_errors_semantic_drain_and_output_stall(d):
    cocotb.start_soon(Clock(d.clk,10,unit="ns").start())
    await reset(d)
    assert await send(d,frame(mold([itch("A",0x55)],BASE_SEQ)),stall_events=True)
    # Semantic failure does not change Mold structural success or sequence commit.
    unknown=bytearray(12); unknown[0]=ord("Z")
    assert await send(d,frame(mold([bytes(unknown)],BASE_SEQ+1))) == []
    assert int(d.b_recovery.value)==1
    assert int(d.b_expected_sequence.value)==BASE_SEQ+2
    d.rearm.value=1; await RisingEdge(d.clk); await FallingEdge(d.clk); d.rearm.value=0
    assert await send(d,frame(mold([itch("A",0x66)],BASE_SEQ)))
    # Wrong session is fatal; a second frame requires explicit rearm.
    assert await send(d,frame(mold_raw(1,b"",BASE_SEQ,session=b"BADSESSION"))) == []
    assert int(d.b_recovery.value)==1
    assert int(d.b_expected_sequence.value)==BASE_SEQ+1


@cocotb.test()
async def two_lane_progress_and_service_measurement(d):
    """Check cursor progress and collect simple B parser service counters."""
    cocotb.start_soon(Clock(d.clk,10,unit="ns").start())
    workloads = [
        ("single_add", [[itch("A",0x1111222233334444,salt=0)]], BASE_SEQ),
        ("two_message", [[itch("A",0x1111222233334444,salt=1),
                           itch("F",0x5555666677778888,salt=2)]], BASE_SEQ),
        ("stateful_types", [[itch("A",0x1111222233334444,salt=3),
                              itch("F",0x5555666677778888,salt=4),
                              itch("E",0x1111222233334444,qty=1,salt=5),
                              itch("C",0x1111222233334444,qty=1,salt=6),
                              itch("X",0x1111222233334444,qty=1,salt=7),
                              itch("U",0x5555666677778888,qty=9,salt=8),
                              itch("D",0x1111222233334444,salt=9)]], BASE_SEQ),
        ("repeated_frames", [[itch("A",0xA000000000000000+i,salt=10+i)] for i in range(5)], BASE_SEQ),
    ]
    for name, frame_messages, seq in workloads:
        await reset(d)
        frames=[frame(mold(msgs,seq+i)) for i,msgs in enumerate(frame_messages)]
        data=b"".join(frames)
        stream=[beat for item in frames for beat in beats(item)]
        expected_events=sum(len(msgs) for msgs in frame_messages)
        idx=0; held=None; cycle=0
        accepted_bytes=0; processed_bytes=0; max_advance=0
        event_cycles=[]; first_accept=None; last_accept=None; stalls=0
        for _ in range(10000):
            await FallingEdge(d.clk)
            if held is None and idx < len(stream):
                held=stream[idx]; d.rx_data.value,d.rx_keep.value,d.rx_last.value=held; d.rx_valid.value=1
            d.a_event_ready.value=1; d.b_event_ready.value=1
            await Timer(1,unit="ns")
            pre_active=int(d.b.beat_active_q.value)
            pre_lane=int(d.b.lane_q.value)
            pre_keep=int(d.b.beat_keep_q.value)
            pre_ingress=int(d.b.ingress_valid.value)
            in_fire=int(d.rx_valid.value) and int(d.rx_ready.value)
            if in_fire:
                if first_accept is None: first_accept=cycle
                last_accept=cycle
                accepted_bytes += int(held[1]).bit_count()
            if int(d.b_event_valid.value) and int(d.b_event_ready.value): event_cycles.append(cycle)
            if int(d.rx_valid.value) and not int(d.rx_ready.value): stalls += 1
            await RisingEdge(d.clk)
            await Timer(1,unit="ns")
            post_active=int(d.b.beat_active_q.value)
            post_lane=int(d.b.lane_q.value)
            if pre_active:
                available=(pre_keep >> pre_lane).bit_count()
                if post_lane > pre_lane: advanced=post_lane-pre_lane
                elif not post_active and post_lane == 0: advanced=available
                else: advanced=0
            elif pre_ingress:
                post_keep=int(d.b.beat_keep_q.value)
                if post_lane: advanced=post_lane
                elif not post_active: advanced=post_keep.bit_count()
                else: advanced=0
            else: advanced=0
            assert 0 <= advanced <= 2, (name,cycle,pre_active,pre_lane,post_active,post_lane,advanced)
            processed_bytes += advanced
            max_advance=max(max_advance,advanced)
            if in_fire:
                idx+=1; held=None; d.rx_valid.value=0
            cycle+=1
            if idx==len(stream) and len(event_cycles)==expected_events: break
        else: raise AssertionError(f"{name} timeout beats={idx}/{len(stream)} events={len(event_cycles)}/{expected_events}")
        assert processed_bytes == len(data), (name,processed_bytes,len(data))
        assert max_advance == 2, (name,max_advance)
        assert len(event_cycles)==expected_events
        intervals=[b-a for a,b in zip(event_cycles,event_cycles[1:])]
        d._log.info("WIRE028B_PARSER_METRIC workload=%s bytes=%d B_event_intervals=%s B_first_frame_to_event=%s max_B_bytes_per_cycle=%d events=%d shared_ingress_stall_cycles=%d",
                    name,accepted_bytes,intervals,
                    (event_cycles[0]-first_accept+1) if event_cycles else None,
                    max_advance,len(event_cycles),stalls)
