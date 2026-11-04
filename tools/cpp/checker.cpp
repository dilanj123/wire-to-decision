#include "checker.hpp"

#include <algorithm>
#include <charconv>
#include <fstream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>

namespace w2d {
namespace {

constexpr uint64_t kMaxU48 = (uint64_t{1} << 48) - 1;
constexpr size_t kSets = 512;

uint64_t number(const std::string& text) {
    if (text.empty() || text.front() == '-') throw std::runtime_error("invalid unsigned integer: " + text);
    size_t used = 0;
    const auto value = std::stoull(text, &used, 0);
    if (used != text.size()) throw std::runtime_error("invalid integer: " + text);
    return value;
}

std::vector<uint8_t> unhex(const std::string& text) {
    if (text.size() % 2 != 0) throw std::runtime_error("hex byte string has odd length");
    std::vector<uint8_t> bytes;
    bytes.reserve(text.size() / 2);
    for (size_t i = 0; i < text.size(); i += 2) {
        unsigned value = 0;
        const auto* begin = text.data() + i;
        const auto* end = begin + 2;
        const auto result = std::from_chars(begin, end, value, 16);
        if (result.ec != std::errc{} || result.ptr != end)
            throw std::runtime_error("invalid hex byte string");
        bytes.push_back(static_cast<uint8_t>(value));
    }
    return bytes;
}

uint64_t be(const std::vector<uint8_t>& bytes, size_t offset, size_t width) {
    if (offset + width > bytes.size()) throw std::runtime_error("truncated field");
    uint64_t value = 0;
    for (size_t i = 0; i < width; ++i) value = (value << 8) | bytes[offset + i];
    return value;
}

bool ipv4_checksum_valid(const std::vector<uint8_t>& ip) {
    uint32_t sum = 0;
    for (size_t i = 0; i < 20; i += 2)
        sum += (static_cast<uint32_t>(ip[i]) << 8) | ip[i + 1];
    while (sum >> 16) sum = (sum & 0xffffU) + (sum >> 16);
    return sum == 0xffffU;
}

struct Order {
    uint64_t reference{};
    uint32_t price{};
    uint32_t quantity{};
    bool sell{};
};

struct Message {
    uint64_t sequence{};
    std::vector<uint8_t> payload;
};

struct MoldResult {
    std::vector<Message> messages;
    bool valid_normal_packet{};
    bool fatal{};
    uint64_t next_sequence{};
};

enum class FrameKind { accepted, filtered, fatal };

struct ParsedFrame {
    FrameKind kind{FrameKind::fatal};
    std::vector<uint8_t> mold;
};

class Engine {
public:
    explicit Engine(Config cfg)
        : cfg_(cfg), expected_sequence_(cfg.expected_sequence), budget_(cfg.initial_budget) {}

    void rearm() {
        for (auto& set : orders_) for (auto& way : set) way.reset();
        bid_ = 0; ask_ = 0; expected_sequence_ = cfg_.expected_sequence;
        previous_ = 0; budget_ = cfg_.initial_budget; decision_count_ = 0;
        quarantined_ = false;
    }

    void set_enabled(bool enabled) { cfg_.enabled = enabled; }

    void process(const std::vector<uint8_t>& frame, size_t frame_index) {
        ++frames_;
        if (quarantined_) return;
        const auto parsed = parse_frame(frame);
        if (parsed.kind == FrameKind::filtered) return;
        if (parsed.kind == FrameKind::fatal) { quarantined_ = true; return; }

        const auto mold = parse_mold(parsed.mold);
        if (mold.valid_normal_packet) expected_sequence_ = mold.next_sequence;
        for (const auto& message : mold.messages) {
            ++messages_;
            const auto decoded = decode(message);
            if (decoded.failure) { quarantined_ = true; break; }
            if (!decoded.event) continue;
            std::string error;
            if (!apply(*decoded.event, error)) { quarantined_ = true; break; }
            evaluate(*decoded.event, frame_index);
        }
        if (mold.fatal) quarantined_ = true;
    }

    void rearm_from(const Config& cfg) {
        cfg_ = cfg;
        rearm();
    }

    RunResult result() const {
        return {decisions_, frames_, messages_, bid_, ask_, expected_sequence_, quarantined_};
    }

private:
    struct Event {
        char type{};
        uint64_t sequence{};
        uint64_t timestamp{};
        uint64_t old_ref{};
        uint64_t new_ref{};
        uint32_t quantity{};
        uint32_t price{};
        bool side_sell{};
        bool has_old{};
        bool has_new{};
        bool has_quantity{};
        bool has_price{};
        bool has_side{};
    };
    struct Decode { std::optional<Event> event; bool failure{}; };

    Config cfg_;
    std::array<std::array<std::optional<Order>, 2>, kSets> orders_{};
    uint64_t bid_{};
    uint64_t ask_{};
    uint64_t expected_sequence_{};
    int64_t previous_{};
    uint32_t budget_{};
    uint32_t decision_count_{};
    bool quarantined_{};
    size_t frames_{};
    size_t messages_{};
    std::vector<Decision> decisions_;

    ParsedFrame parse_frame(const std::vector<uint8_t>& frame) const {
        auto filtered = [] { return ParsedFrame{FrameKind::filtered, {}}; };
        auto fatal = [] { return ParsedFrame{FrameKind::fatal, {}}; };
        if (frame.size() < 14) return fatal();
        if (be(frame, 12, 2) != 0x0800) return filtered();
        std::vector<uint8_t> ip(frame.begin() + 14, frame.end());
        if (ip.size() < 20) return fatal();
        if ((ip[0] >> 4) != 4 || (ip[0] & 0x0f) != 5) return filtered();
        const size_t total = static_cast<size_t>(be(ip, 2, 2));
        if (total < 20 || total > ip.size()) return fatal();
        ip.resize(total);
        if (!ipv4_checksum_valid(ip)) return fatal();
        const uint16_t flags_fragment = static_cast<uint16_t>(be(ip, 6, 2));
        if ((flags_fragment & 0x2000U) || (flags_fragment & 0x1fffU)) return fatal();
        if (be(ip, 16, 4) != cfg_.destination_ip) return filtered();
        if (ip[9] != 17) return filtered();
        if (ip.size() < 28) return fatal();
        const size_t udp_length = static_cast<size_t>(be(ip, 24, 2));
        if (udp_length < 8 || udp_length != ip.size() - 20) return fatal();
        if (be(ip, 22, 2) != cfg_.destination_port) return filtered();
        if (be(ip, 26, 2) != 0) return filtered();
        return {FrameKind::accepted,
                std::vector<uint8_t>(ip.begin() + 28, ip.end())};
    }

    MoldResult parse_mold(const std::vector<uint8_t>& bytes) const {
        MoldResult out{{}, false, false, expected_sequence_};
        if (bytes.size() < 20) { out.fatal = true; return out; }
        if (!std::equal(cfg_.session.begin(), cfg_.session.end(), bytes.begin()) ||
            be(bytes, 10, 8) != expected_sequence_) {
            out.fatal = true; return out;
        }
        const uint16_t count = static_cast<uint16_t>(be(bytes, 18, 2));
        if (count == 0) {
            out.fatal = bytes.size() != 20;
            return out;
        }
        if (count == 0xffff) {
            out.fatal = true;
            return out;
        }
        size_t cursor = 20;
        for (uint32_t i = 0; i < count; ++i) {
            if (cursor + 2 > bytes.size()) { out.fatal = true; return out; }
            const size_t length = static_cast<size_t>(be(bytes, cursor, 2));
            cursor += 2;
            if (cursor + length > bytes.size()) { out.fatal = true; return out; }
            Message message{be(bytes, 10, 8) + i,
                            std::vector<uint8_t>(bytes.begin() + cursor,
                                                 bytes.begin() + cursor + length)};
            out.messages.push_back(std::move(message));
            cursor += length;
        }
        if (cursor != bytes.size()) { out.fatal = true; return out; }
        out.valid_normal_packet = true;
        out.next_sequence = expected_sequence_ + count;
        return out;
    }

    Decode decode(const Message& message) const {
        const auto& p = message.payload;
        if (p.empty()) return {{}, true};
        const char type = static_cast<char>(p[0]);
        size_t expected_length = 0;
        switch (type) {
        case 'A': expected_length = 36; break;
        case 'F': expected_length = 40; break;
        case 'E': expected_length = 31; break;
        case 'C': expected_length = 36; break;
        case 'X': expected_length = 23; break;
        case 'D': expected_length = 19; break;
        case 'U': expected_length = 35; break;
        case 'P': expected_length = 44; break;
        default: return {{}, true};
        }
        if (p.size() != expected_length) return {{}, true};
        if (type == 'P') return {{}, false};
        const uint16_t locate = static_cast<uint16_t>(be(p, 1, 2));
        if (locate != cfg_.tracked_locate) return {{}, false};

        Event e{};
        e.type = type;
        e.sequence = message.sequence;
        e.timestamp = be(p, 5, 6);
        if (type == 'A' || type == 'F') {
            if (cfg_.symbol_check && !std::equal(cfg_.symbol.begin(), cfg_.symbol.end(), p.begin() + 24))
                return {{}, true};
            if (p[19] != 'B' && p[19] != 'S') return {{}, true};
            e.new_ref = be(p, 11, 8); e.quantity = static_cast<uint32_t>(be(p, 20, 4));
            e.price = static_cast<uint32_t>(be(p, 32, 4)); e.side_sell = p[19] == 'S';
            e.has_new = e.has_quantity = e.has_price = e.has_side = true;
        } else if (type == 'E' || type == 'C' || type == 'X') {
            e.old_ref = be(p, 11, 8); e.quantity = static_cast<uint32_t>(be(p, 19, 4));
            e.has_old = e.has_quantity = true;
        } else if (type == 'D') {
            e.old_ref = be(p, 11, 8); e.has_old = true;
        } else if (type == 'U') {
            e.old_ref = be(p, 11, 8); e.new_ref = be(p, 19, 8);
            e.quantity = static_cast<uint32_t>(be(p, 27, 4));
            e.price = static_cast<uint32_t>(be(p, 31, 4));
            e.has_old = e.has_new = e.has_quantity = e.has_price = true;
        }
        if ((e.has_quantity && e.quantity == 0) || (type == 'U' && e.quantity == 0))
            return {{}, true};
        return {e, false};
    }

    bool apply(const Event& e, std::string& error) {
        if (e.type == 'A' || e.type == 'F') return add(e, error);
        if (e.type == 'E' || e.type == 'C' || e.type == 'X')
            return reduce(e, e.type == 'X' ? "OVER_CANCEL" : "OVER_EXECUTE", error);
        if (e.type == 'D') return erase(e, error);
        if (e.type == 'U') return replace(e, error);
        error = "UNSUPPORTED_EVENT";
        return false;
    }

    bool add(const Event& e, std::string& error) {
        auto& set = orders_[order_set_index(e.new_ref)];
        for (const auto& way : set)
            if (way && way->reference == e.new_ref) { error = "DUPLICATE_REFERENCE"; return false; }
        auto it = std::find_if(set.begin(), set.end(), [](const auto& way) { return !way; });
        if (it == set.end()) { error = "COLLISION_CAPACITY"; return false; }
        uint64_t& total = e.side_sell ? ask_ : bid_;
        if (total > kMaxU48 - e.quantity) { error = "AGGREGATE_RANGE"; return false; }
        *it = Order{e.new_ref, e.price, e.quantity, e.side_sell};
        total += e.quantity;
        return true;
    }

    std::optional<std::pair<size_t, size_t>> find(uint64_t reference) const {
        const size_t index = order_set_index(reference);
        for (size_t way = 0; way < 2; ++way)
            if (orders_[index][way] && orders_[index][way]->reference == reference)
                return std::pair{index, way};
        return std::nullopt;
    }

    bool reduce(const Event& e, const std::string& over_error, std::string& error) {
        const auto location = find(e.old_ref);
        if (!location) { error = "UNKNOWN_REFERENCE"; return false; }
        auto& order = orders_[location->first][location->second];
        if (e.quantity > order->quantity) { error = over_error; return false; }
        uint64_t& total = order->sell ? ask_ : bid_;
        if (total < e.quantity) { error = "AGGREGATE_RANGE"; return false; }
        order->quantity -= e.quantity;
        total -= e.quantity;
        if (order->quantity == 0) order.reset();
        return true;
    }

    bool erase(const Event& e, std::string& error) {
        const auto location = find(e.old_ref);
        if (!location) { error = "UNKNOWN_REFERENCE"; return false; }
        auto& order = orders_[location->first][location->second];
        uint64_t& total = order->sell ? ask_ : bid_;
        if (total < order->quantity) { error = "AGGREGATE_RANGE"; return false; }
        total -= order->quantity;
        order.reset();
        return true;
    }

    bool replace(const Event& e, std::string& error) {
        const auto old_location = find(e.old_ref);
        if (!old_location) { error = "UNKNOWN_REFERENCE"; return false; }
        const auto new_location = find(e.new_ref);
        if (new_location && e.new_ref != e.old_ref) { error = "NEW_REFERENCE_CONFLICT"; return false; }
        const auto old = *orders_[old_location->first][old_location->second];
        const size_t new_index = order_set_index(e.new_ref);
        size_t new_way = 2;
        for (size_t way = 0; way < 2; ++way) {
            const bool is_old = old_location->first == new_index && old_location->second == way;
            if (!orders_[new_index][way] || is_old) { new_way = way; break; }
        }
        if (new_way == 2) { error = "COLLISION_CAPACITY"; return false; }
        uint64_t& total = old.sell ? ask_ : bid_;
        if (total < old.quantity) { error = "AGGREGATE_RANGE"; return false; }
        const uint64_t base = total - old.quantity;
        if (base > kMaxU48 - e.quantity) { error = "AGGREGATE_RANGE"; return false; }
        // All checks precede state changes, so failure is atomic.
        orders_[old_location->first][old_location->second].reset();
        orders_[new_index][new_way] = Order{e.new_ref, e.price, e.quantity, old.sell};
        total = base + e.quantity;
        return true;
    }

    void evaluate(const Event& e, size_t frame_index) {
        const int64_t current = static_cast<int64_t>(bid_) - static_cast<int64_t>(ask_);
        if (cfg_.enabled && budget_ > 0) {
            const int64_t threshold = static_cast<int64_t>(cfg_.threshold);
            if (previous_ < threshold && current >= threshold) {
                decisions_.push_back({"BUY", e.sequence, e.timestamp, current, frame_index});
                --budget_; ++decision_count_;
            } else if (previous_ > -threshold && current <= -threshold) {
                decisions_.push_back({"SELL", e.sequence, e.timestamp, current, frame_index});
                --budget_; ++decision_count_;
            }
        }
        previous_ = current;
    }
};

} // namespace

uint16_t order_set_index(uint64_t reference) {
    uint16_t index = 0;
    for (unsigned shift = 0; shift <= 54; shift += 9)
        index ^= static_cast<uint16_t>((reference >> shift) & 0x1ffU);
    index ^= static_cast<uint16_t>((reference >> 63) & 1U);
    return static_cast<uint16_t>(index & 0x1ffU);
}

Replay read_replay(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open replay: " + path);
    Replay replay{};
    std::string line;
    bool have_header = false, have_config = false;
    while (std::getline(input, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream row(line);
        std::string command;
        row >> command;
        if (!have_header) {
            if (command != "WIRE_REPLAY_V1") throw std::runtime_error("expected WIRE_REPLAY_V1 header");
            have_header = true;
            continue;
        }
        if (command == "CONFIG") {
            std::map<std::string, std::string> fields;
            std::string field;
            while (row >> field) {
                const auto split = field.find('=');
                if (split == std::string::npos) throw std::runtime_error("invalid CONFIG field: " + field);
                fields[field.substr(0, split)] = field.substr(split + 1);
            }
            auto required = [&fields](const std::string& key) -> const std::string& {
                const auto it = fields.find(key);
                if (it == fields.end()) throw std::runtime_error("CONFIG missing " + key);
                return it->second;
            };
            replay.config.destination_ip = static_cast<uint32_t>(number(required("destination_ip")));
            replay.config.destination_port = static_cast<uint16_t>(number(required("destination_port")));
            const auto session = unhex(required("session"));
            const auto symbol = unhex(required("symbol"));
            if (session.size() != 10 || symbol.size() != 8) throw std::runtime_error("session/symbol width mismatch");
            std::copy(session.begin(), session.end(), replay.config.session.begin());
            std::copy(symbol.begin(), symbol.end(), replay.config.symbol.begin());
            replay.config.expected_sequence = number(required("expected_sequence"));
            replay.config.tracked_locate = static_cast<uint16_t>(number(required("tracked_locate")));
            replay.config.symbol_check = number(required("symbol_check")) != 0;
            replay.config.threshold = number(required("threshold"));
            replay.config.initial_budget = static_cast<uint32_t>(number(required("budget")));
            replay.config.enabled = number(required("enable")) != 0;
            if (number(required("destination_ip")) > 0xffffffffULL ||
                number(required("destination_port")) > 0xffffULL ||
                number(required("tracked_locate")) > 0xffffULL ||
                number(required("budget")) > 0xffffffffULL ||
                number(required("symbol_check")) > 1 || number(required("enable")) > 1)
                throw std::runtime_error("CONFIG field exceeds its declared width");
            if (replay.config.threshold > kMaxU48) throw std::runtime_error("threshold exceeds 48-bit range");
            have_config = true;
        } else if (command == "FRAME") {
            if (!have_config) throw std::runtime_error("CONFIG must precede FRAME");
            std::string hex;
            if (!(row >> hex)) throw std::runtime_error("FRAME missing hex bytes");
            std::string extra;
            if (row >> extra) throw std::runtime_error("unexpected FRAME data");
            replay.frames.push_back(unhex(hex));
            replay.actions.push_back("FRAME");
        } else if (command == "REARM") {
            replay.actions.push_back("REARM");
        } else if (command == "ENABLE") {
            std::string value;
            if (!(row >> value) || (value != "0" && value != "1")) throw std::runtime_error("ENABLE expects 0 or 1");
            replay.actions.push_back("ENABLE " + value);
        } else {
            throw std::runtime_error("unknown replay command: " + command);
        }
    }
    if (!have_header || !have_config || replay.frames.empty()) throw std::runtime_error("incomplete replay");
    return replay;
}

ActualLog read_actual_log(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open actual RTL log: " + path);
    ActualLog actual{};
    std::string line;
    bool have_header = false;
    while (std::getline(input, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream row(line);
        std::string command;
        row >> command;
        if (!have_header) {
            if (command != "WIRE_RTL_LOG_V1") throw std::runtime_error("expected WIRE_RTL_LOG_V1 header");
            have_header = true;
            continue;
        }
        std::map<std::string, std::string> fields;
        std::string field;
        while (row >> field) {
            const auto split = field.find('=');
            if (split == std::string::npos) throw std::runtime_error("invalid RTL log field: " + field);
            fields[field.substr(0, split)] = field.substr(split + 1);
        }
        auto get = [&fields](const std::string& key) -> uint64_t {
            const auto it = fields.find(key);
            if (it == fields.end()) throw std::runtime_error("RTL log missing " + key);
            return number(it->second);
        };
        if (command == "DECISION") {
            const auto action = fields.find("action");
            if (action == fields.end() || (action->second != "BUY" && action->second != "SELL"))
                throw std::runtime_error("invalid RTL decision action");
            actual.decisions.push_back({action->second, get("mold_sequence"),
                get("itch_timestamp"), static_cast<int64_t>(std::stoll(fields.at("imbalance"))),
                0, get("cycle")});
        } else if (command == "LATENCY") {
            actual.latencies.push_back({get("cycle"), get("l1"), get("l2"), get("l3")});
        } else if (command == "STATE") {
            actual.bid_total = get("bid_total"); actual.ask_total = get("ask_total");
            actual.expected_sequence = get("expected_sequence");
            actual.quarantined = get("quarantined") != 0;
        } else {
            throw std::runtime_error("unknown RTL log record: " + command);
        }
    }
    if (!have_header) throw std::runtime_error("empty RTL log");
    return actual;
}

RunResult run_replay(const Replay& replay) {
    Engine engine(replay.config);
    size_t frame_index = 0;
    for (const auto& action : replay.actions) {
        if (action == "REARM") engine.rearm();
        else if (action.rfind("ENABLE ", 0) == 0) engine.set_enabled(action.back() == '1');
        else if (action == "FRAME") {
            engine.process(replay.frames.at(frame_index), frame_index);
            ++frame_index;
        }
    }
    return engine.result();
}

} // namespace w2d
