"""
KrishiSarth Core Constants
This file defines all threshold constants used for AI decisions, 
safety cutoffs, and system-wide constraints as specified in PROJECT_RULES.md.
"""

# AI Decision Thresholds (PROJECT_RULES.md Section 5.9)
# Confidence >= 0.80 -> auto-execute the suggested irrigation/fertigation
AI_AUTO_EXECUTE_THRESHOLD = 0.80

# Confidence 0.60–0.79 -> flag the decision for manual review by the farmer
AI_MANUAL_REVIEW_THRESHOLD = 0.60

# Moisture < 25% -> trigger rule-based fallback irrigation if AI/Weather APIs fail
AI_MOISTURE_RULE_THRESHOLD = 0.25

# Resource Constraints
# Block irrigation if water tank level drops below 10%
TANK_CRITICAL_PCT = 10

# Maximum 2 zones can be irrigated concurrently at the same farm to maintain pressure
MAX_CONCURRENT_PUMPS = 2

# Timing and Timeouts
# Maximum seconds to wait for a relay activation acknowledgement from the field nodes
PUMP_ACK_TIMEOUT_S = 10

# Stagger zone starts by 300s (5 min) during batch irrigation to prevent surge draw
ZONE_START_STAGGER_S = 300

# Security / Brute Force Protection
# Maximum failed login attempts before account lockout
BRUTE_FORCE_MAX_ATTEMPTS = 5

# Window in seconds for counting failed attempts (10 minutes)
BRUTE_FORCE_WINDOW_S = 600

# Duration of account lockout after exceeding max attempts (15 minutes)
BRUTE_FORCE_LOCKOUT_S = 900
