#include "checker.hpp"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>

namespace {

struct Distribution {
    uint64_t minimum{};
    double median{};
    uint64_t p95{};
    uint64_t maximum{};
};

Distribution distribution(std::vector<uint64_t> values) {
    if (values.empty()) return {};
    std::sort(values.begin(), values.end());
    const size_t n = values.size();
    const double median = n % 2 ? static_cast<double>(values[n / 2])
        : (static_cast<double>(values[n / 2 - 1]) + values[n / 2]) / 2.0;
    const size_t p95_index = std::max<size_t>(1, static_cast<size_t>(std::ceil(0.95 * n))) - 1;
    return {values.front(), median, values[p95_index], values.back()};
}

void write_distribution(std::ostream& out, const Distribution& d) {
    out << "{\"min\":" << d.minimum << ",\"median\":" << d.median
        << ",\"p95\":" << d.p95 << ",\"max\":" << d.maximum << "}";
}

int compare(const std::string& replay_path, const std::string& rtl_path,
            const std::string& summary_path) {
    const auto replay = w2d::read_replay(replay_path);
    const auto actual = w2d::read_actual_log(rtl_path);
    const auto expected = w2d::run_replay(replay);
    size_t mismatches = 0;
    auto mismatch = [&mismatches](const std::string& message) {
        ++mismatches;
        std::cerr << "MISMATCH: " << message << '\n';
    };

    if (expected.decisions.size() != actual.decisions.size()) {
        std::string context = "decision count expected=" + std::to_string(expected.decisions.size()) +
                              " actual=" + std::to_string(actual.decisions.size());
        if (expected.decisions.size() > actual.decisions.size()) {
            const auto& e = expected.decisions[actual.decisions.size()];
            context += "; missing at frame=" + std::to_string(e.frame_index) + " message-seq=" +
                       std::to_string(e.mold_sequence) + " expected=" + e.action +
                       ",imbalance=" + std::to_string(e.imbalance);
        } else if (actual.decisions.size() > expected.decisions.size()) {
            const auto& a = actual.decisions[expected.decisions.size()];
            context += "; unexpected RTL message-seq=" + std::to_string(a.mold_sequence) +
                       " actual=" + a.action + ",imbalance=" + std::to_string(a.imbalance);
        }
        mismatch(context);
    }
    const size_t shared = std::min(expected.decisions.size(), actual.decisions.size());
    for (size_t i = 0; i < shared; ++i) {
        const auto& e = expected.decisions[i];
        const auto& a = actual.decisions[i];
        if (e.action != a.action || e.mold_sequence != a.mold_sequence ||
            e.itch_timestamp != a.itch_timestamp || e.imbalance != a.imbalance) {
            mismatch("decision[" + std::to_string(i) + "] frame=" +
                std::to_string(e.frame_index) + " expected={" + e.action + ",seq=" +
                std::to_string(e.mold_sequence) + ",ts=" + std::to_string(e.itch_timestamp) +
                ",imb=" + std::to_string(e.imbalance) + "} actual={" + a.action + ",seq=" +
                std::to_string(a.mold_sequence) + ",ts=" + std::to_string(a.itch_timestamp) +
                ",imb=" + std::to_string(a.imbalance) + "}");
        }
    }
    if (!actual.bid_total || !actual.ask_total || !actual.expected_sequence || !actual.quarantined) {
        mismatch("RTL log must include one STATE record with aggregates, expected sequence and quarantine");
    } else {
        if (*actual.bid_total != expected.bid_total)
            mismatch("bid_total expected=" + std::to_string(expected.bid_total) +
                     " actual=" + std::to_string(*actual.bid_total));
        if (*actual.ask_total != expected.ask_total)
            mismatch("ask_total expected=" + std::to_string(expected.ask_total) +
                     " actual=" + std::to_string(*actual.ask_total));
        if (*actual.expected_sequence != expected.expected_sequence)
            mismatch("expected_sequence expected=" + std::to_string(expected.expected_sequence) +
                     " actual=" + std::to_string(*actual.expected_sequence));
        if (*actual.quarantined != expected.quarantined)
            mismatch("quarantined expected=" + std::to_string(expected.quarantined) +
                     " actual=" + std::to_string(*actual.quarantined));
    }

    std::vector<uint64_t> l1, l2, l3;
    if (actual.latencies.size() != actual.decisions.size())
        mismatch("latency samples expected one per RTL decision: decisions=" +
                 std::to_string(actual.decisions.size()) + " samples=" +
                 std::to_string(actual.latencies.size()));
    const size_t latency_shared = std::min(actual.latencies.size(), actual.decisions.size());
    for (size_t i = 0; i < latency_shared; ++i) {
        if (actual.latencies[i].cycle != actual.decisions[i].cycle)
            mismatch("latency cycle does not match decision cycle at decision[" +
                     std::to_string(i) + "]");
    }
    for (const auto& latency : actual.latencies) {
        l1.push_back(latency.l1); l2.push_back(latency.l2); l3.push_back(latency.l3);
    }
    const auto d1 = distribution(l1), d2 = distribution(l2), d3 = distribution(l3);
    std::ofstream summary(summary_path);
    if (!summary) throw std::runtime_error("cannot write summary: " + summary_path);
    summary << "{\n  \"frames_checked\": " << expected.frames_checked
            << ",\n  \"messages_checked\": " << expected.messages_checked
            << ",\n  \"decisions_compared\": " << shared
            << ",\n  \"mismatches\": " << mismatches
            << ",\n  \"replay_pass\": " << (mismatches == 0 ? "true" : "false")
            << ",\n  \"latency_sample_count\": " << actual.latencies.size()
            << ",\n  \"latency_cycles\": {\n    \"L1\": ";
    write_distribution(summary, d1);
    summary << ",\n    \"L2\": "; write_distribution(summary, d2);
    summary << ",\n    \"L3\": "; write_distribution(summary, d3);
    summary << "\n  },\n  \"final_state\": {\"bid_total\": " << expected.bid_total
            << ", \"ask_total\": " << expected.ask_total
            << ", \"expected_sequence\": " << expected.expected_sequence
            << ", \"quarantined\": " << (expected.quarantined ? "true" : "false")
            << "}\n}\n";

    std::cout << "frames=" << expected.frames_checked << " messages=" << expected.messages_checked
              << " decisions=" << shared << " mismatches=" << mismatches
              << " replay=" << (mismatches == 0 ? "PASS" : "FAIL")
              << " latency_samples=" << actual.latencies.size() << '\n';
    std::cout << "L1 cycles min/median/p95/max=" << d1.minimum << '/' << d1.median << '/'
              << d1.p95 << '/' << d1.maximum << '\n';
    std::cout << "L2 cycles min/median/p95/max=" << d2.minimum << '/' << d2.median << '/'
              << d2.p95 << '/' << d2.maximum << '\n';
    std::cout << "L3 cycles min/median/p95/max=" << d3.minimum << '/' << d3.median << '/'
              << d3.p95 << '/' << d3.maximum << '\n';
    return mismatches == 0 ? 0 : 1;
}

} // namespace

int main(int argc, char** argv) {
    try {
        if (argc == 3 && std::string(argv[1]) == "run") {
            const auto result = w2d::run_replay(w2d::read_replay(argv[2]));
            std::cout << "frames=" << result.frames_checked << " messages=" << result.messages_checked
                      << " decisions=" << result.decisions.size() << " bid=" << result.bid_total
                      << " ask=" << result.ask_total << " expected_sequence=" << result.expected_sequence
                      << " quarantined=" << result.quarantined << '\n';
            for (const auto& decision : result.decisions)
                std::cout << decision.action << " seq=" << decision.mold_sequence
                          << " timestamp=" << decision.itch_timestamp
                          << " imbalance=" << decision.imbalance << '\n';
            return 0;
        }
        if (argc == 5 && std::string(argv[1]) == "compare")
            return compare(argv[2], argv[3], argv[4]);
        std::cerr << "Usage:\n  w2d_checker run REPLAY\n"
                  << "  w2d_checker compare REPLAY RTL_LOG SUMMARY_JSON\n";
        return 2;
    } catch (const std::exception& error) {
        std::cerr << "w2d_checker: " << error.what() << '\n';
        return 2;
    }
}
