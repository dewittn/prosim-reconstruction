"""
Default configuration values for PROSIM simulation.

These values were derived from reverse-engineering the original PROSIM
simulation using spreadsheet analysis of DECS/REPT file pairs from a
2004 college course.

Values marked with (verified) have high confidence from multiple data points.
Values marked with (estimated) are reasonable assumptions that should be
validated and may need calibration.
Values marked with (derived-2024) were discovered through forensic analysis
of multiple REPT files in December 2024.
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
# REJECT RATE - QUALITY BUDGET RELATIONSHIP (derived-2024)
# =============================================================================

# The reject rate is NOT constant - it varies with quality budget!
# Evidence from cross-week analysis:
#   Quality Budget $750  -> Reject Rate ~17.8%
#   Quality Budget $850  -> Reject Rate ~15.0%
#   Quality Budget $1000 -> Reject Rate ~10.6%
REJECT_RATE_CONFIG: dict[str, float] = {
    "base_rate": 0.178,  # Reject rate at $750 quality budget
    "base_budget": 750.0,  # Reference quality budget
    "reduction_per_dollar": 0.00029,  # Each dollar above base reduces rate by this amount
    "minimum_rate": 0.05,  # Floor - can't reduce rejects below 5%
}


def calculate_reject_rate(quality_budget: float) -> float:
    """
    Calculate reject rate based on quality budget.

    Formula derived from forensic analysis (2024):
    reject_rate = 0.178 - ((quality_budget - 750) * 0.00029)

    Examples:
        $750 budget  -> 17.8% rejects
        $1000 budget -> 10.6% rejects
        $1500 budget -> ~5% rejects (floor)
    """
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
# OPERATOR TRAINING SYSTEM (derived-2024)
# =============================================================================

# Operators have TWO hidden stats that affect production:
# 1. Time Efficiency: What % of scheduled hours are productive
# 2. Production Proficiency: What % of standard production rate achieved

OPERATOR_TIME_EFFICIENCY: dict[str, float] = {
    # Productive Hours / Scheduled Hours
    "untrained_min": 0.64,  # New hires start here
    "untrained_max": 0.70,
    "partial_trained_min": 0.80,
    "partial_trained_max": 0.95,
    "trained_min": 0.95,
    "trained_max": 1.00,
    "improvement_per_week": 0.08,  # ~5-10% improvement per week worked
    "weeks_to_full_training": 4,  # Weeks of continuous work to be fully trained
}

OPERATOR_PROFICIENCY: dict[str, float] = {
    # Actual Production Rate / Standard Production Rate
    "untrained_min": 0.65,
    "untrained_max": 0.85,
    "trained_min": 0.90,
    "trained_max": 1.05,
    "expert_max": 1.25,  # Some operators consistently outperform (Op 3 was 122-125%!)
    "improvement_per_week": 0.05,  # Proficiency improves with experience
}

# Legacy operator efficiency (combined) for backwards compatibility
OPERATOR_EFFICIENCY: dict[str, float] = {
    "trained_min": 0.95,
    "trained_max": 1.00,
    "untrained_min": 0.60,
    "untrained_max": 0.90,
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
# LABOR RATES (derived-2024)
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
# MACHINE REPAIR - MAINTENANCE BUDGET RELATIONSHIP (derived-2024)
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
    prob = MACHINE_REPAIR_CONFIG["base_probability"] - (
        (maintenance_budget - MACHINE_REPAIR_CONFIG["base_maintenance_budget"])
        * MACHINE_REPAIR_CONFIG["probability_reduction_per_dollar"]
    )
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
        "time_efficiency": OPERATOR_TIME_EFFICIENCY,
        "proficiency": OPERATOR_PROFICIENCY,
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
