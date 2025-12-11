"""
Default configuration values for PROSIM simulation.

These values were derived from reverse-engineering the original PROSIM
simulation using spreadsheet analysis of DECS/REPT file pairs from a
2004 college course.

Values marked with (verified) have high confidence from multiple data points.
Values marked with (estimated) are reasonable assumptions that should be
validated and may need calibration.
Values marked with (derived-2025) were discovered through forensic analysis
of multiple REPT files in December 2025.

IMPORTANT CALIBRATION NOTE:
The original spreadsheet was tuned for ~Week 20 of a 24-week simulation.
Early weeks (1-4) reflect "blind" decision-making with no understanding of
the game mechanics, so data from those weeks may show artifacts of poor
decisions rather than true simulation behavior. Week 12+ data is more
reliable for algorithm calibration as it reflects informed, optimized play.
"""

from typing import Any

# =============================================================================
# PRODUCTION RATES (verified)
# =============================================================================

# Parts Department: raw materials -> parts
PARTS_PRODUCTION_RATES: dict[str, int] = {
    "X'": 60,  # BASE parts per productive hour (modified by operator proficiency)
    "Y'": 50,
    "Z'": 40,
}

# Assembly Department: parts -> products
ASSEMBLY_PRODUCTION_RATES: dict[str, int] = {
    "X": 40,  # BASE units per productive hour (modified by operator proficiency)
    "Y": 30,
    "Z": 20,
}

# =============================================================================
# REJECT RATE - QUALITY BUDGET RELATIONSHIP (derived-2025, VERIFIED Dec 2025)
# =============================================================================

# The reject rate is NOT constant - it varies with quality budget!
# VERIFIED: DECS14 specified $750 budget, REPT14 showed exactly 17.8% rejects.
#
# Empirical data from 2004 spreadsheet (Graph-Table 1) shows LOGARITHMIC relationship:
#   Quality Budget $750  -> Reject Rate 15.14%
#   Quality Budget $850  -> Reject Rate 13.02%
#   Quality Budget $900  -> Reject Rate 12.10%
#   Quality Budget $1000 -> Reject Rate 10.00%
#   Quality Budget $1200 -> Reject Rate 7.94%
#   Quality Budget $1300 -> Reject Rate 7.36%
#   Quality Budget $2000 -> Reject Rate 4.00%
#   Quality Budget $2500 -> Reject Rate ~1.6% (floor region)
#
# The relationship follows diminishing returns - each dollar buys less reduction.
# Linear approximation is used below for simplicity, but true relationship is logarithmic.
REJECT_RATE_CONFIG: dict[str, float] = {
    "base_rate": 0.1514,  # Reject rate at $750 quality budget (from empirical data)
    "base_budget": 750.0,  # Reference quality budget
    "reduction_per_dollar": 0.00029,  # Linear approximation (actual relationship is logarithmic)
    "minimum_rate": 0.015,  # Floor - can't reduce rejects below ~1.5% (verified from Week 16 data)
}


def calculate_reject_rate(quality_budget: float, use_logarithmic: bool = True) -> float:
    """
    Calculate reject rate based on quality budget.

    The relationship is LOGARITHMIC (diminishing returns) based on empirical
    data from 2004 spreadsheet analysis. A linear approximation is available
    for simpler calculations.

    Logarithmic formula (fitted to empirical data):
        reject_rate = 0.904 - 0.114 * ln(quality_budget)

    Linear approximation:
        reject_rate = 0.1514 - ((quality_budget - 750) * 0.00029)

    Examples:
        $750 budget  -> 15.1% rejects
        $1000 budget -> 10.0% rejects
        $2000 budget -> 4.0% rejects
        $2500 budget -> ~1.5% rejects (floor)

    Args:
        quality_budget: The quality planning budget in dollars
        use_logarithmic: If True, use logarithmic formula (default). If False, use linear.

    Returns:
        Reject rate as a decimal (e.g., 0.10 for 10%)
    """
    import math

    if use_logarithmic:
        # Logarithmic fit from empirical data: rate = 0.904 - 0.114 * ln(budget)
        rate = 0.904 - 0.114 * math.log(quality_budget)
    else:
        # Linear approximation
        rate = REJECT_RATE_CONFIG["base_rate"] - (
            (quality_budget - REJECT_RATE_CONFIG["base_budget"])
            * REJECT_RATE_CONFIG["reduction_per_dollar"]
        )

    return max(REJECT_RATE_CONFIG["minimum_rate"], rate)


# Legacy constant for backwards compatibility
REJECT_RATE: float = 0.178  # At default $750 quality budget

# =============================================================================
# BILL OF MATERIALS (verified)
# =============================================================================

BOM: dict[str, dict[str, int]] = {
    "X": {"X'": 1},
    "Y": {"Y'": 1},
    "Z": {"Z'": 1},
}

# Raw materials per part (estimated - needs calibration)
RAW_MATERIALS_PER_PART: dict[str, float] = {
    "X'": 1.0,  # RM units per part
    "Y'": 1.0,
    "Z'": 1.0,
}

# =============================================================================
# LEAD TIMES (verified from presentations)
# =============================================================================

LEAD_TIMES: dict[str, int] = {
    "raw_materials_regular": 3,  # weeks
    "raw_materials_expedited": 1,  # weeks
    "purchased_parts": 1,  # weeks
}

EXPEDITED_SHIPPING_COST: float = 1200.0  # Premium for expedited orders

# =============================================================================
# OPERATOR TRAINING SYSTEM (VERIFIED Dec 2025)
# =============================================================================
#
# Training system discovered through forensic analysis of ProsimTable.xls and
# verified against XTC game state files with 0.2% average error.
#
# Each operator has:
# 1. Quality Tier (0-9): Fixed innate ability assigned at hire
# 2. Training Level (0-10): Advances with weeks of continuous work
#
# Efficiency = TRAINING_MATRIX[quality_tier][training_level]
#
# OPERATOR CEILING (Dec 2025):
# Each operator has a maximum efficiency ceiling determined by Quality Tier.
# Training improves efficiency but CANNOT exceed the tier's maximum (rightmost
# column in the matrix). Analysis of multiple game runs showed:
#
#   - Operator 3: Always expert (103-112% proficiency) across ALL games
#   - Operator 4: Always low tier (~60% ceiling)
#   - Operator 5: Always low tier (~55% ceiling)
#
# This suggests starting operators (1-9) have FIXED profiles consistent across
# all game instances. Hired operators (10+) appear to have randomized tiers.
#
# Strategic implication: No amount of training makes a low-tier operator expert.

# Training level names for reference
TRAINING_LEVELS: list[str] = [
    "Untrained", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J"
]

# Exact training matrix from reverse-engineered spreadsheet (2004)
# Verified against XTC game state files (Dec 2025)
# Row = Quality Tier (0-9), Column = Training Level (0-10)
# Values are efficiency percentages
TRAINING_MATRIX: dict[int, list[int]] = {
    #        Untr,  A,   B,   C,   D,   E,   F,   G,   H,   I,   J
    0: [      20,  61,  79,  89,  96, 100, 103, 106, 108, 109, 109],
    1: [      21,  63,  81,  91,  98, 103, 106, 109, 111, 112, 112],
    2: [      21,  64,  82,  93, 100, 104, 108, 110, 112, 114, 114],
    3: [      21,  64,  83,  94, 101, 106, 109, 112, 114, 116, 116],
    4: [      21,  65,  84,  95, 102, 107, 110, 113, 115, 117, 117],
    5: [      22,  66,  85,  96, 103, 108, 111, 114, 116, 118, 118],
    6: [      22,  66,  85,  96, 104, 108, 112, 115, 117, 118, 118],
    7: [      22,  66,  86,  97, 104, 109, 112, 115, 117, 119, 119],
    8: [      22,  67,  86,  97, 104, 109, 113, 116, 118, 120, 120],
    9: [      22,  67,  87,  98, 105, 110, 113, 116, 118, 120, 120],
}


def get_operator_efficiency(quality_tier: int, training_level: int) -> float:
    """
    Get operator efficiency based on quality tier and training level.

    Args:
        quality_tier: 0-9, operator's innate ability (fixed at hire)
        training_level: 0-10, weeks of continuous work (0=untrained, 10=J=max)

    Returns:
        Efficiency as decimal (e.g., 1.03 for 103%)

    Example:
        >>> get_operator_efficiency(5, 4)  # Tier 5, Level D
        1.03

    Verified against XTC game state files (Dec 2025) with 0.2% avg error.
    """
    tier = max(0, min(9, quality_tier))
    level = max(0, min(10, training_level))
    return TRAINING_MATRIX[tier][level] / 100.0


# Legacy constants for backwards compatibility
OPERATOR_TIME_EFFICIENCY: dict[str, float] = {
    "untrained_min": 0.20,  # From matrix: Tier 0, Level 0
    "untrained_max": 0.22,  # From matrix: Tier 9, Level 0
    "trained_min": 1.09,    # From matrix: Tier 0, Level J
    "trained_max": 1.20,    # From matrix: Tier 9, Level J
    "weeks_to_full_training": 10,  # Levels 0-10 (Untrained through J)
}

OPERATOR_PROFICIENCY: dict[str, float] = {
    # Quality tier determines efficiency ceiling - not a separate multiplier
    "tier_min": 0,
    "tier_max": 9,
}

OPERATOR_EFFICIENCY: dict[str, float] = {
    "trained_min": 1.09,
    "trained_max": 1.20,
    "untrained_min": 0.20,
    "untrained_max": 0.22,
}

# Starting operator profiles (discovered Dec 2025, refined with proficiency Dec 2025)
# These appear to be FIXED across all game instances based on cross-game analysis.
#
# TWO-COMPONENT EFFICIENCY MODEL:
#   Actual_Efficiency = Training_Matrix[tier][level] × Proficiency
#
# - quality_tier: Determines training matrix row (0-9)
# - proficiency: Fixed multiplier at hire (derived from ProsimTable.xls Week 16 data)
#
# Proficiency was calculated as: Actual_Efficiency / Training_Matrix[tier][level]
# For example, Op 3 at tier 9, level I (118%) achieved 132.4% → proficiency = 1.122
#
# Hired operators (10+) have randomized tiers and proficiency.
STARTING_OPERATOR_PROFILES: dict[int, dict[str, any]] = {
    1: {"quality_tier": 6, "proficiency": 1.039},  # Normal performer
    2: {"quality_tier": 5, "proficiency": 1.097},  # Normal performer
    3: {"quality_tier": 9, "proficiency": 1.122},  # EXPERT - highest proficiency!
    4: {"quality_tier": 5, "proficiency": 1.093},  # Normal performer
    5: {"quality_tier": 5, "proficiency": 1.028},  # Normal performer
    6: {"quality_tier": 9, "proficiency": 0.836},  # Low proficiency despite high tier
    7: {"quality_tier": 9, "proficiency": 0.934},  # Below average proficiency
    8: {"quality_tier": 2, "proficiency": 0.850},  # Low tier, low proficiency (estimated)
    9: {"quality_tier": 2, "proficiency": 0.900},  # Low tier, low proficiency (estimated)
}

# =============================================================================
# SETUP TIME (estimated)
# =============================================================================

SETUP_TIME_HOURS: dict[str, float] = {
    "parts_department": 2.0,  # Hours to change part type
    "assembly_department": 2.0,
}

# =============================================================================
# WORKFORCE COSTS (verified from week1.txt and ProSim_intro.ppt)
# =============================================================================

WORKFORCE_COSTS: dict[str, float] = {
    "hiring_cost": 2700.0,  # per new hire (verified)
    "layoff_cost_per_week": 200.0,  # per week not scheduled (verified)
    "termination_cost": 400.0,  # after 2 consecutive weeks unscheduled (verified)
    "training_cost_per_worker": 1000.0,  # estimated per training session
}

# =============================================================================
# LABOR RATES (derived-2025)
# =============================================================================

# From ProSim_intro.ppt: "9 operators needed: $10/hour"
LABOR_RATES: dict[str, float] = {
    "regular_hourly": 10.0,  # $ per hour (verified from PPT)
    "overtime_multiplier": 1.5,  # Time and a half above 40 hours (verified from PPT)
    "minimum_hours": 20.0,  # Minimum hours per operator per week (from PPT)
}

# =============================================================================
# FIXED COSTS (verified from week1.txt)
# =============================================================================

FIXED_COSTS: dict[str, float] = {
    "fixed_expense_per_week": 1500.0,
}

# =============================================================================
# MACHINE REPAIR - MAINTENANCE BUDGET RELATIONSHIP (derived-2025)
# =============================================================================

# Machine repair is stochastic but influenced by maintenance budget
# Evidence:
#   Maint Budget $500, Repair occurred ($400)
#   Maint Budget $500, No repair
#   Maint Budget $550, No repair
MACHINE_REPAIR_CONFIG: dict[str, Any] = {
    "cost_per_repair": 400.0,  # Constant cost per repair event (verified)
    "base_probability": 0.15,  # Base probability per machine per week (~10-15%)
    "base_maintenance_budget": 500.0,
    "probability_reduction_per_dollar": 0.0001,  # Higher budget = lower probability
}


def calculate_repair_probability(maintenance_budget: float) -> float:
    """
    Calculate machine repair probability based on maintenance budget.

    Hypothesis: Higher maintenance budget reduces repair probability.

    Examples:
        $500 budget  -> ~10% repair probability
        $1000 budget -> ~5% repair probability
        $1500 budget -> ~0% repair probability
    """
    base_prob = float(MACHINE_REPAIR_CONFIG["base_probability"])
    base_budget = float(MACHINE_REPAIR_CONFIG["base_maintenance_budget"])
    reduction_rate = float(MACHINE_REPAIR_CONFIG["probability_reduction_per_dollar"])

    prob = base_prob - ((maintenance_budget - base_budget) * reduction_rate)
    return max(0.0, min(1.0, prob))


# Legacy constant for backwards compatibility
MACHINE_REPAIR: dict[str, Any] = {
    "probability_per_machine_per_week": 0.10,
    "cost_per_repair": 400.0,
}

# =============================================================================
# CARRYING COSTS (estimated - needs calibration)
# =============================================================================

CARRYING_COST_RATES: dict[str, float] = {
    "raw_materials": 0.01,  # per unit per week
    "parts": 0.05,  # per part per week
    "products": 0.10,  # per product per week
}

# =============================================================================
# EQUIPMENT USAGE RATES (estimated - needs derivation)
# =============================================================================

EQUIPMENT_RATES: dict[str, float] = {
    "parts_department": 100.0,  # $ per hour
    "assembly_department": 80.0,  # $ per hour
}

# =============================================================================
# DEMAND PARAMETERS (from presentations)
# =============================================================================

DEMAND: dict[str, Any] = {
    "forecast_std_dev_weeks_out": {
        4: 300,  # 4+ weeks out
        3: 300,
        2: 200,
        1: 100,  # 1 week out
        0: 0,  # shipping week (known)
    },
    # Trend values for EWMA forecasting (from prosim_forecasting.htm)
    "trend_values": {
        "X": 328,
        "Y": 220,
        "Z": 169,
    },
}

# =============================================================================
# SIMULATION STRUCTURE (verified)
# =============================================================================

SIMULATION: dict[str, Any] = {
    "parts_machines": 4,
    "assembly_machines": 5,
    "starting_operators": 9,  # From PPT: "9 operators needed"
    "max_scheduled_hours": 50,  # per machine per week
    "regular_hours": 40,
    "shipping_frequency": 4,  # every 4 weeks (monthly)
}

# =============================================================================
# AGGREGATE CONFIG
# =============================================================================

DEFAULT_CONFIG: dict[str, Any] = {
    "production": {
        "parts_rates": PARTS_PRODUCTION_RATES,
        "assembly_rates": ASSEMBLY_PRODUCTION_RATES,
        "reject_rate": REJECT_RATE,
        "reject_rate_config": REJECT_RATE_CONFIG,
        "bom": BOM,
        "raw_materials_per_part": RAW_MATERIALS_PER_PART,
        "setup_time": SETUP_TIME_HOURS,
    },
    "logistics": {
        "lead_times": LEAD_TIMES,
        "expedited_shipping_cost": EXPEDITED_SHIPPING_COST,
    },
    "workforce": {
        "training_matrix": TRAINING_MATRIX,  # VERIFIED: 11 levels × 10 tiers
        "training_levels": TRAINING_LEVELS,
        "time_efficiency": OPERATOR_TIME_EFFICIENCY,  # Legacy
        "proficiency": OPERATOR_PROFICIENCY,  # Legacy
        "efficiency": OPERATOR_EFFICIENCY,  # Legacy
        "costs": WORKFORCE_COSTS,
    },
    "equipment": {
        "repair": MACHINE_REPAIR,
        "repair_config": MACHINE_REPAIR_CONFIG,
        "rates": EQUIPMENT_RATES,
    },
    "costs": {
        "fixed": FIXED_COSTS,
        "carrying": CARRYING_COST_RATES,
        "labor": LABOR_RATES,
    },
    "demand": DEMAND,
    "simulation": SIMULATION,
}
