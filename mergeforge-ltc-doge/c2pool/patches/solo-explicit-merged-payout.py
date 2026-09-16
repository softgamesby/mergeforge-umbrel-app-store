#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/src")

def replace(rel, old, new):
    path = root / rel
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(
            f"{rel}: expected patch context exactly once, found {text.count(old)}"
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"patched {rel}")

# ---------------------------------------------------------------------
# Stratum rate monitor: retain explicit merged-chain payout scripts with
# each accepted pseudoshare. This preserves payout identity historically
# even after a miner session disconnects.
# ---------------------------------------------------------------------

replace(
    "src/core/stratum_server.hpp",
    """#include <set>
#include <array>

#include <deque>
""",
    """#include <set>
#include <array>
#include <vector>

#include <deque>
"""
)

replace(
    "src/core/stratum_server.hpp",
    """        std::array<uint8_t, 20> pubkey_hash;
        std::string user;
        bool dead;
""",
    """        std::array<uint8_t, 20> pubkey_hash;
        std::string user;
        bool dead;
        std::map<uint32_t, std::vector<unsigned char>> explicit_merged_scripts;
"""
)

replace(
    "src/core/stratum_server.hpp",
    """    void add_datum(double work, const std::array<uint8_t, 20>& pubkey_hash,
                   const std::string& user, bool dead);
""",
    """    void add_datum(double work, const std::array<uint8_t, 20>& pubkey_hash,
                   const std::string& user, bool dead,
                   const std::map<uint32_t, std::vector<unsigned char>>& explicit_merged_scripts = {});
"""
)

replace(
    "src/core/stratum_server.hpp",
    """using AddrRateMap = std::unordered_map<std::array<uint8_t, 20>, double, PubkeyHashHasher>;
""",
    """using AddrRateMap = std::unordered_map<std::array<uint8_t, 20>, double, PubkeyHashHasher>;
using MergedAddrRateMap = std::map<std::vector<unsigned char>, double>;
"""
)

replace(
    "src/core/stratum_server.hpp",
    """    AddrRateMap get_local_addr_rates() const;

    /// Per-user hashrate + dead hashrate from RateMonitor.
""",
    """    AddrRateMap get_local_addr_rates() const;

    /// Per-merged-chain payout-script hashrate aggregation.
    /// Explicit miner-provided scripts are preserved; miners without an
    /// explicit merged address fall back to P2PKH using the primary hash160.
    MergedAddrRateMap get_local_merged_addr_rates(uint32_t chain_id) const;

    /// Per-user hashrate + dead hashrate from RateMonitor.
"""
)

replace(
    "src/core/stratum_server.hpp",
    """    void record_pseudoshare(double work, const std::array<uint8_t, 20>& pubkey_hash,
                            const std::string& user, bool dead);
""",
    """    void record_pseudoshare(double work, const std::array<uint8_t, 20>& pubkey_hash,
                            const std::string& user, bool dead,
                            const std::map<uint32_t, std::vector<unsigned char>>& explicit_merged_scripts = {});
"""
)

replace(
    "src/core/stratum_server.cpp",
    """void RateMonitor::add_datum(double work, const std::array<uint8_t, 20>& pubkey_hash,
                            const std::string& user, bool dead) {
""",
    """void RateMonitor::add_datum(double work, const std::array<uint8_t, 20>& pubkey_hash,
                            const std::string& user, bool dead,
                            const std::map<uint32_t, std::vector<unsigned char>>& explicit_merged_scripts) {
"""
)

replace(
    "src/core/stratum_server.cpp",
    """        datums_.push_back({t, work, pubkey_hash, user, dead});
""",
    """        datums_.push_back({t, work, pubkey_hash, user, dead, explicit_merged_scripts});
"""
)

replace(
    "src/core/stratum_server.cpp",
    """    return rates;
}

std::pair<std::unordered_map<std::string, double>,
""",
    """    return rates;
}

MergedAddrRateMap StratumServer::get_local_merged_addr_rates(uint32_t chain_id) const
{
    auto [datums, dt] = local_addr_rate_monitor_.get_datums_in_last();
    MergedAddrRateMap rates;
    if (dt <= 0) return rates;

    for (const auto& d : datums) {
        std::vector<unsigned char> script;

        auto explicit_it = d.explicit_merged_scripts.find(chain_id);
        if (explicit_it != d.explicit_merged_scripts.end()) {
            script = explicit_it->second;
        } else {
            // Existing c2pool solo fallback: same hash160 encoded as P2PKH
            // on the merged chain.
            script = {0x76, 0xa9, 0x14};
            script.insert(script.end(), d.pubkey_hash.begin(), d.pubkey_hash.end());
            script.push_back(0x88);
            script.push_back(0xac);
        }

        if (!script.empty())
            rates[script] += d.work / dt;
    }
    return rates;
}

std::pair<std::unordered_map<std::string, double>,
"""
)

replace(
    "src/core/stratum_server.cpp",
    """void StratumServer::record_pseudoshare(double work, const std::array<uint8_t, 20>& pubkey_hash,
                                        const std::string& user, bool dead)
{
    local_rate_monitor_.add_datum(work, pubkey_hash, user, dead);
    local_addr_rate_monitor_.add_datum(work, pubkey_hash, user, dead);
}
""",
    """void StratumServer::record_pseudoshare(double work, const std::array<uint8_t, 20>& pubkey_hash,
                                        const std::string& user, bool dead,
                                        const std::map<uint32_t, std::vector<unsigned char>>& explicit_merged_scripts)
{
    local_rate_monitor_.add_datum(work, pubkey_hash, user, dead, explicit_merged_scripts);
    local_addr_rate_monitor_.add_datum(work, pubkey_hash, user, dead, explicit_merged_scripts);
}
"""
)

# ---------------------------------------------------------------------
# During Stratum submit, distinguish explicit merged addresses from
# c2pool's auto-derived entries. Auto-derived entries equal username_.
# ---------------------------------------------------------------------

replace(
    "src/core/stratum_server.cpp",
    """    std::map<uint32_t, std::vector<unsigned char>> merged_scripts;
    for (const auto& [chain_id, addr] : merged_addresses_) {
        std::string atype;
        auto h160 = address_to_hash160(addr, atype);
        if (h160.size() == 40) {
            auto script = hash160_to_merged_script(h160, atype);
            if (!script.empty())
                merged_scripts[chain_id] = std::move(script);
        }
    }
""",
    """    std::map<uint32_t, std::vector<unsigned char>> merged_scripts;
    std::map<uint32_t, std::vector<unsigned char>> explicit_merged_scripts;
    for (const auto& [chain_id, addr] : merged_addresses_) {
        std::string atype;
        auto h160 = address_to_hash160(addr, atype);
        if (h160.size() == 40) {
            auto script = hash160_to_merged_script(h160, atype);
            if (!script.empty()) {
                merged_scripts[chain_id] = script;
                if (addr != username_)
                    explicit_merged_scripts[chain_id] = std::move(script);
            }
        }
    }
"""
)

replace(
    "src/core/stratum_server.cpp",
    """        server_->record_pseudoshare(work, pubkey_hash_, username_, is_dead);
""",
    """        server_->record_pseudoshare(
            work, pubkey_hash_, username_, is_dead, explicit_merged_scripts);
"""
)

# ---------------------------------------------------------------------
# WebServer forwarding API used by the LTC integrated/solo engine.
# ---------------------------------------------------------------------

replace(
    "src/core/web_server.hpp",
    """    std::map<std::array<uint8_t, 20>, double> get_local_addr_rates() const;

    // Stratum server control methods
""",
    """    std::map<std::array<uint8_t, 20>, double> get_local_addr_rates() const;
    std::map<std::vector<unsigned char>, double>
        get_local_merged_addr_rates(uint32_t chain_id) const;

    // Stratum server control methods
"""
)

replace(
    "src/core/web_server.cpp",
    """    return result;
}

void WebServer::trigger_work_refresh()
""",
    """    return result;
}

std::map<std::vector<unsigned char>, double>
WebServer::get_local_merged_addr_rates(uint32_t chain_id) const
{
    if (!stratum_server_) return {};
    return stratum_server_->get_local_merged_addr_rates(chain_id);
}

void WebServer::trigger_work_refresh()
"""
)

# ---------------------------------------------------------------------
# Solo AuxPoW payout provider: use merged-chain-specific payout scripts
# instead of reconstructing every payout from the primary LTC hash160.
# ---------------------------------------------------------------------

replace(
    "src/c2pool/main_ltc.cpp",
    """                        uint64_t miner_pool = coinbase_value - owner_fee_amount - donation_amount;
                        auto rates = web_server.get_local_addr_rates();
                        double total_rate = 0;
                        for (auto& [_, rate] : rates) total_rate += rate;

                        if (total_rate > 0) {
                            for (auto& [pubkey_hash, rate] : rates) {
                                uint64_t amount = static_cast<uint64_t>(miner_pool * rate / total_rate);
                                if (amount == 0) continue;
                                std::vector<unsigned char> script = {0x76, 0xa9, 0x14};
                                script.insert(script.end(), pubkey_hash.begin(), pubkey_hash.end());
                                script.push_back(0x88);
                                script.push_back(0xac);
                                result.emplace_back(std::move(script), amount);
                            }
                        } else if (!owner_script_mm.empty()) {
""",
    """                        uint64_t miner_pool = coinbase_value - owner_fee_amount - donation_amount;
                        auto rates = web_server.get_local_merged_addr_rates(chain_id);
                        double total_rate = 0;
                        for (auto& [_, rate] : rates) total_rate += rate;

                        if (total_rate > 0) {
                            for (auto& [script, rate] : rates) {
                                uint64_t amount = static_cast<uint64_t>(miner_pool * rate / total_rate);
                                if (amount == 0 || script.empty()) continue;
                                result.emplace_back(script, amount);
                            }
                        } else if (!owner_script_mm.empty()) {
"""
)


# solo startup null-p2p fix
replace(
    "src/c2pool/main_ltc.cpp",
    """            {
                auto [initial_ver, initial_desired] = auto_ratchet->get_share_version(
                    p2p_node->tracker(), uint256());
                auto donation_script = ltc::PoolConfig::get_donation_script(initial_ver);
""",
    """            {
                int64_t initial_ver = 35;
                if (p2p_node) {
                    auto [iv, idv] = auto_ratchet->get_share_version(
                        p2p_node->tracker(), uint256());
                    (void)idv;
                    initial_ver = iv;
                }
                auto donation_script = ltc::PoolConfig::get_donation_script(initial_ver);
"""
)

print("solo explicit merged-payout patch: all contexts matched")
