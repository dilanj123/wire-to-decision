import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model" / "python"))
from wire_to_decision.oracle import ReferenceOracle
from wire_to_decision.types import ModelConfig

DEST_IP=0xC6336407; DEST_PORT=0x1234; LOC=0x2345
SESSION=b"W2DTEST001"; SEQ=0x1020304050607080; SYMBOL=b"ALPH    "


def put(b,o,n,v): b[o:o+n]=v.to_bytes(n,"big")

def checksum(b):
    if len(b)&1: b+=b"\0"
    x=sum(int.from_bytes(b[i:i+2],"big") for i in range(0,len(b),2))
    while x>>16: x=(x&0xffff)+(x>>16)
    return (~x)&0xffff

def add(ref,qty=10,price=100,side=b"B"):
    b=bytearray(36); b[0]=ord("A"); put(b,1,2,LOC); put(b,3,2,0x1234)
    put(b,5,6,0x010203040506); put(b,11,8,ref); b[19]=side[0]
    put(b,20,4,qty); b[24:32]=SYMBOL; put(b,32,4,price); return bytes(b)

def message(kind, old_ref=0, new_ref=0, qty=1, price=100, side=b"B", salt=0):
    sizes={"A":36,"F":40,"E":31,"C":36,"X":23,"D":19,"U":35}
    b=bytearray(sizes[kind]); b[0]=ord(kind); put(b,1,2,LOC); put(b,3,2,0x2200+salt)
    put(b,5,6,0x010203040500+salt)
    if kind in "AF":
        put(b,11,8,old_ref); b[19]=side[0]; put(b,20,4,qty); b[24:32]=SYMBOL; put(b,32,4,price)
        if kind=="F": b[36:40]=b"MPID"
    elif kind in "ECX":
        put(b,11,8,old_ref); put(b,19,4,qty)
        if kind=="C": b[23]=ord("Y"); put(b,24,4,0xDEADBEEF); b[28:36]=b"XYZ12345"
    elif kind=="D": put(b,11,8,old_ref)
    elif kind=="U":
        put(b,11,8,old_ref); put(b,19,8,new_ref); put(b,27,4,qty); put(b,31,4,price)
    return bytes(b)

def make_frame(messages,seq):
    mold=SESSION+seq.to_bytes(8,"big")+len(messages).to_bytes(2,"big")
    mold+=b"".join(len(m).to_bytes(2,"big")+m for m in messages)
    udp=bytearray(8); put(udp,0,2,0xbeef); put(udp,2,2,DEST_PORT); put(udp,4,2,8+len(mold))
    ip=bytearray(20); ip[0]=0x45; put(ip,2,2,20+len(udp)+len(mold)); ip[8]=64; ip[9]=17
    put(ip,16,4,DEST_IP); put(ip,10,2,checksum(bytes(ip)))
    return bytes.fromhex("0201020304050A0B0C0D0E0F")+b"\x08\x00"+bytes(ip)+bytes(udp)+mold

def beats(data):
    out=[]
    for off in range(0,len(data),8):
        p=data[off:off+8]
        out.append((sum(x<<(8*i) for i,x in enumerate(p)),(1<<len(p))-1,int(off+len(p)==len(data))))
    return out

def signed49(value):
    return value-(1<<49) if value&(1<<48) else value


@cocotb.test()
async def shared_book_decision_matches_oracle(d):
    cocotb.start_soon(Clock(d.clk,10,unit="ns").start())
    pins={"rst":1,"rearm":0,"cfg_destination_ipv4":DEST_IP,"cfg_destination_udp_port":DEST_PORT,
          "cfg_active_session":int.from_bytes(SESSION,"big"),"cfg_expected_sequence":SEQ,
          "cfg_tracked_stock_locate":LOC,"cfg_symbol_check_enable":1,
          "cfg_expected_stock_symbol":int.from_bytes(SYMBOL,"big"),"cfg_decision_threshold":10,
          "cfg_initial_budget":3,"decision_enable":1,"rx_data":0,"rx_keep":0,
          "rx_valid":0,"rx_last":0,"decision_ready":1}
    for k,v in pins.items(): getattr(d,k).value=v
    await RisingEdge(d.clk); await FallingEdge(d.clk); d.rst.value=0
    data=make_frame([add(0x1122334455667788)],SEQ); stream=beats(data); idx=0; held=None; decision=None
    for cycle in range(3000):
        await FallingEdge(d.clk)
        if held is None and idx<len(stream):
            held=stream[idx]; d.rx_data.value,d.rx_keep.value,d.rx_last.value=held; d.rx_valid.value=1
        await Timer(1,unit="ns")
        if int(d.decision_valid.value) and int(d.decision_ready.value):
            x=int(d.decision_signed_imbalance.value); x=x-(1<<49) if x&(1<<48) else x
            decision=(int(d.decision_action.value),int(d.decision_mold_sequence.value),
                      int(d.decision_itch_timestamp.value),x)
        fire=int(d.rx_valid.value) and int(d.rx_ready.value)
        await RisingEdge(d.clk)
        if fire:
            idx+=1; held=None; d.rx_valid.value=0
        if idx==len(stream) and decision is not None: break
    assert idx==len(stream) and decision is not None
    expected=ReferenceOracle(ModelConfig(DEST_IP,DEST_PORT,LOC,True,SYMBOL,SESSION,SEQ,10,3,True)).process_frame(data)
    assert len(expected.decisions)==1
    py=expected.decisions[0]
    assert decision==(int(py.action.value=="SELL"),py.trigger_mold_sequence,py.itch_timestamp,py.signed_imbalance)
    assert int(d.bid_total.value)==10 and int(d.ask_total.value)==0
    assert int(d.remaining_budget.value)==2 and int(d.decision_count.value)==1
    assert int(d.current_expected_sequence.value)==SEQ+1
    assert int(d.parser_recovery_required.value)==0 and int(d.book_recovery_required.value)==0


@cocotb.test()
async def b_parser_book_workloads_and_cycle_metrics(d):
    """Compare bounded workloads with the oracle and count real beat/lane progress."""
    cocotb.start_soon(Clock(d.clk,10,unit="ns").start())
    workloads=[
        ("single_add_buy", [[message("A",0x1001,qty=10,price=100,salt=1)]], SEQ),
        ("two_message", [[message("A",0x1101,qty=10,price=101,salt=2),
                           message("E",0x1101,qty=1,salt=3)]], SEQ),
        ("stateful_A_F_E_C_X_U_D", [[message("A",0x2001,qty=10,price=100,salt=10)],
             [message("F",0x2002,qty=20,price=101,side=b"S",salt=11)],
             [message("E",0x2002,qty=5,salt=12)], [message("C",0x2002,qty=5,salt=13)],
             [message("X",0x2002,qty=5,salt=14)],
             [message("U",0x2001,new_ref=0x8877665544332211+5,qty=20,price=105,salt=15)],
             [message("D",0x8877665544332211+5,salt=16)]], SEQ),
        ("repeated_frames", [[add(0xA000000000000000+i,qty=i+1,price=100+i)] for i in range(5)], SEQ),
    ]
    for name, packet_messages, seq in workloads:
        pins={"rst":1,"rearm":0,"cfg_destination_ipv4":DEST_IP,"cfg_destination_udp_port":DEST_PORT,
              "cfg_active_session":int.from_bytes(SESSION,"big"),"cfg_expected_sequence":seq,
              "cfg_tracked_stock_locate":LOC,"cfg_symbol_check_enable":1,
              "cfg_expected_stock_symbol":int.from_bytes(SYMBOL,"big"),"cfg_decision_threshold":10,
              "cfg_initial_budget":32,"decision_enable":1,"rx_data":0,"rx_keep":0,
              "rx_valid":0,"rx_last":0,"decision_ready":1}
        for k,v in pins.items(): getattr(d,k).value=v
        await RisingEdge(d.clk); await FallingEdge(d.clk); d.rst.value=0
        frames=[make_frame(msgs,seq+i) for i,msgs in enumerate(packet_messages)]
        stream=[]; frame_start_message_seqs={}
        for i,raw in enumerate(frames):
            frame_start_message_seqs[len(stream)]=[seq+i+j for j in range(len(packet_messages[i]))]
            stream.extend(beats(raw))
        oracle=ReferenceOracle(ModelConfig(DEST_IP,DEST_PORT,LOC,True,SYMBOL,SESSION,seq,10,32,True))
        expected=[]
        for raw in frames:
            result=oracle.process_frame(raw)
            assert result.accepted and not result.quarantined
            expected.extend(result.decisions)
        idx=0; held=None; cycle=0; first_rx=None; frame_start_cycles={}; accepted_bytes=0; ingress_stall=0
        events=0; commits=0; event_rows=[]; decision_cycles=[]; observed=[]
        first_byte_cycles={}; final_byte_cycles={}
        processed=0; max_lanes=0; idle_after=0
        for _ in range(12000):
            await FallingEdge(d.clk)
            if held is None and idx<len(stream):
                held=stream[idx]; d.rx_data.value,d.rx_keep.value,d.rx_last.value=held; d.rx_valid.value=1
            await Timer(1,unit="ns")
            pre_active=int(d.parser.beat_active_q.value); pre_lane=int(d.parser.lane_q.value)
            pre_keep=int(d.parser.beat_keep_q.value); pre_ingress=int(d.parser.ingress_valid.value)
            rx_fire=int(d.rx_valid.value) and int(d.rx_ready.value)
            if rx_fire:
                if first_rx is None: first_rx=cycle
                if idx in frame_start_message_seqs:
                    for message_seq in frame_start_message_seqs[idx]: frame_start_cycles[message_seq]=cycle
                accepted_bytes+=int(held[1]).bit_count()
            elif int(d.rx_valid.value): ingress_stall+=1
            event_fire=int(d.parser.event_valid_q.value) and int(d.parser.event_ready.value)
            if event_fire:
                events+=1; event_rows.append((cycle,int(d.parser.event_sequence_q.value)))
            if int(d.commit_valid.value) and int(d.commit_ready.value): commits+=1
            if int(d.decision_valid.value) and int(d.decision_ready.value):
                decision_cycles.append(cycle)
                observed.append((int(d.decision_action.value),int(d.decision_mold_sequence.value),
                    int(d.decision_itch_timestamp.value),signed49(int(d.decision_signed_imbalance.value))))
            pre_index=int(d.parser.msg_index_q.value)
            pre_remaining=int(d.parser.itch_remaining_q.value)
            pre_sequence=int(d.parser.packet_sequence_q.value)+int(d.parser.messages_done_q.value)
            await RisingEdge(d.clk); await Timer(1,unit="ns")
            post_active=int(d.parser.beat_active_q.value); post_lane=int(d.parser.lane_q.value)
            post_index=int(d.parser.msg_index_q.value)
            post_remaining=int(d.parser.itch_remaining_q.value)
            post_done=int(d.parser.messages_done_q.value)
            if pre_index==0 and post_index>0:
                first_byte_cycles.setdefault(pre_sequence,cycle)
            if 0<pre_remaining<=2 and post_remaining==0:
                final_byte_cycles.setdefault(pre_sequence,cycle)
            if pre_active:
                available=(pre_keep>>pre_lane).bit_count()
                advanced=(post_lane-pre_lane) if post_lane>pre_lane else (available if not post_active and post_lane==0 else 0)
            elif pre_ingress:
                post_keep=int(d.parser.beat_keep_q.value)
                advanced=post_lane if post_lane else (post_keep.bit_count() if not post_active else 0)
            else: advanced=0
            assert advanced<=2, (name,cycle,advanced)
            processed+=advanced; max_lanes=max(max_lanes,advanced)
            if rx_fire:
                idx+=1; held=None; d.rx_valid.value=0
            cycle+=1
            idle=(idx==len(stream) and int(d.parser.state_q.value)==0 and
                  int(d.parser.beat_active_q.value)==0 and int(d.parser.ingress.count_q.value)==0 and
                  not int(d.parser.event_valid_q.value))
            if idle and commits==events and cycle>0: idle_after+=1
            else: idle_after=0
            if idle_after>=3 and len(decision_cycles)==len(expected): break
        else: raise AssertionError(f"{name} timed out input={idx}/{len(stream)} decisions={decision_cycles}")
        got=decision_cycles
        # Compare the complete decision tuple at the public ready/valid boundary.
        expected_tuples=[(int(x.action.value=="SELL"),x.trigger_mold_sequence,
                          x.itch_timestamp,x.signed_imbalance) for x in expected]
        assert observed==expected_tuples, (name,observed,expected_tuples)
        assert processed==sum(len(f) for f in frames), (name,processed,sum(len(f) for f in frames))
        assert accepted_bytes==processed and max_lanes==2
        assert int(d.bid_total.value)==oracle.book.bid_total and int(d.ask_total.value)==oracle.book.ask_total
        assert int(d.current_expected_sequence.value)==oracle.framing_state.expected_sequence
        assert int(d.remaining_budget.value)==oracle.decision_model.current_budget
        assert int(d.decision_count.value)==oracle.decision_model.decision_count
        assert len(got)==len(expected) and commits==events
        # Decision tuples are checked in the baseline directed test; here compare
        # count/order timing and final state for the longer service workloads.
        elapsed=cycle-first_rx if first_rx is not None else cycle
        event_cycles=[x[0] for x in event_rows]
        event_intervals=[b-a for a,b in zip(event_cycles,event_cycles[1:])]
        decision_intervals=[b-a for a,b in zip(got,got[1:])]
        event_cycle_by_seq={event_seq:event_cycle for event_cycle,event_seq in event_rows}
        l1=[event_cycle-first_byte_cycles[event_seq]
            for event_cycle,event_seq in event_rows if event_seq in first_byte_cycles]
        l2=[decision_cycle-final_byte_cycles[item.trigger_mold_sequence]
            for decision_cycle,item in zip(got,expected)
            if item.trigger_mold_sequence in final_byte_cycles]
        assert len(l1)==events and len(l2)==len(got), (name,first_byte_cycles,final_byte_cycles,event_cycle_by_seq)
        l3=[decision_cycle-frame_start_cycles[item.trigger_mold_sequence]+1
            for decision_cycle,item in zip(got,expected)]
        d._log.info("WIRE028B_FULL_METRIC workload=%s accepted_bytes=%d elapsed_cycles=%d bytes_per_cycle=%.4f max_parser_bytes_per_cycle=%d event_handshakes=%d decisions=%d event_intervals=%s decision_intervals=%s ingress_stall_cycles=%d L1_first_ITCH_byte_to_event_cycles=%s L2_final_ITCH_byte_to_decision_cycles=%s L3_frame_to_decision_cycles=%s",
                    name,accepted_bytes,elapsed,accepted_bytes/elapsed,max_lanes,events,len(got),
                    event_intervals,decision_intervals,ingress_stall,l1,l2,
                    l3)
