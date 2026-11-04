#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace w2d {

struct Config {
    uint32_t destination_ip{};
    uint16_t destination_port{};
    std::array<uint8_t, 10> session{};
    uint64_t expected_sequence{};
    uint16_t tracked_locate{};
    std::array<uint8_t, 8> symbol{};
    bool symbol_check{true};
    uint64_t threshold{};
    uint32_t initial_budget{};
    bool enabled{true};
};

struct Decision {
    std::string action;
    uint64_t mold_sequence{};
    uint64_t itch_timestamp{};
    int64_t imbalance{};
    size_t frame_index{};
    uint64_t cycle{};
};

struct Latency {
    uint64_t cycle{};
    uint64_t l1{};
    uint64_t l2{};
    uint64_t l3{};
};

struct ActualLog {
    std::vector<Decision> decisions;
    std::vector<Latency> latencies;
    std::optional<uint64_t> bid_total;
    std::optional<uint64_t> ask_total;
    std::optional<uint64_t> expected_sequence;
    std::optional<bool> quarantined;
};

struct RunResult {
    std::vector<Decision> decisions;
    size_t frames_checked{};
    size_t messages_checked{};
    uint64_t bid_total{};
    uint64_t ask_total{};
    uint64_t expected_sequence{};
    bool quarantined{};
};

struct Replay {
    Config config;
    std::vector<std::vector<uint8_t>> frames;
    std::vector<std::string> actions;
};

Replay read_replay(const std::string& path);
ActualLog read_actual_log(const std::string& path);
RunResult run_replay(const Replay& replay);
uint16_t order_set_index(uint64_t reference);

} // namespace w2d
