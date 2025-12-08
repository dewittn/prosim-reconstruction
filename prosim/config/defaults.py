"""
Default configuration values for PROSIM simulation.

These values were derived from reverse-engineering the original PROSIM
simulation using spreadsheet analysis of DECS/REPT file pairs from a
2004 college course.

Values marked with (verified) have high confidence from multiple data points.
Values marked with (estimated) are reasonable assumptions that should be
validated and may need calibration.
"""

from typing import Any

# Production rates (verified)
# Parts Department: raw materials -> parts
PARTS_PRODUCTION_RATES: dict[str, int] = {
    "X'": 60,  # parts per productive hour
    "Y'": 50,
    "Z'": 40,
}

# Assembly Department: parts -> products
ASSEMBLY_PRODUCTION_RATES: dict[str, int] = {
    "X": 40,  # units per productive hour
    "Y": 30,
    "Z": 20,
}

# Reject rate (verified: ~17.8% across all observed production)
REJECT_RATE: float = 0.178

# Bill of Materials (verified: 1:1 for all products)
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

# Lead times (verified from presentations)
LEAD_TIMES: dict[str, int] = {
    "raw_materials_regular": 3,  # weeks
    "raw_materials_expedited": 1,  # weeks
    "purchased_parts": 1,  # weeks
}

# Expedited shipping premium (verified)
EXPEDITED_SHIPPING_COST: float = 1200.0

# Operator efficiency (estimated - needs calibration)
OPERATOR_EFFICIENCY: dict[str, float] = {
    "trained_min": 0.95,
    "trained_max": 1.00,
    "untrained_min": 0.60,
    "untrained_max": 0.90,
}

# Setup time when changing part type (estimated)
SETUP_TIME_HOURS: dict[str, float] = {
    "parts_department": 2.0,
    "assembly_department": 2.0,
}

# Workforce costs (verified from week1.txt)
WORKFORCE_COSTS: dict[str, float] = {
    "hiring_cost": 2700.0,  # per new hire
    "layoff_cost_per_week": 200.0,  # per week not scheduled
    "termination_cost": 400.0,  # after 2 consecutive weeks unscheduled
    "training_cost_per_worker": 1000.0,  # estimated per training session
}

# Fixed costs (verified from week1.txt)
FIXED_COSTS: dict[str, float] = {
    "fixed_expense_per_week": 1500.0,
}

# Machine repair (estimated - stochastic element)
MACHINE_REPAIR: dict[str, Any] = {
    "probability_per_machine_per_week": 0.10,  # 10% chance
    "cost_per_repair": 400.0,
}

# Carrying costs (estimated - needs calibration from data)
CARRYING_COST_RATES: dict[str, float] = {
    "raw_materials": 0.01,  # per unit per week
    "parts": 0.05,  # per part per week
    "products": 0.10,  # per product per week
}

# Labor rates (estimated - needs derivation from cost data)
LABOR_RATES: dict[str, float] = {
    "regular_hourly": 20.0,  # $ per hour
    "overtime_multiplier": 1.5,
}

# Equipment usage rates (estimated - needs derivation)
EQUIPMENT_RATES: dict[str, float] = {
    "parts_department": 100.0,  # $ per hour
    "assembly_department": 80.0,  # $ per hour
}

# Demand parameters (from presentations)
DEMAND: dict[str, Any] = {
    "forecast_std_dev_weeks_out": {
        4: 300,  # 4+ weeks out
        3: 300,
        2: 200,
        1: 100,  # 1 week out
        0: 0,  # shipping week (known)
    },
}

# Simulation structure
SIMULATION: dict[str, Any] = {
    "parts_machines": 4,
    "assembly_machines": 5,
    "max_scheduled_hours": 50,  # per machine per week
    "regular_hours": 40,
    "shipping_frequency": 4,  # every 4 weeks (monthly)
}


# Aggregate all defaults into a single config dict
DEFAULT_CONFIG: dict[str, Any] = {
    "production": {
        "parts_rates": PARTS_PRODUCTION_RATES,
        "assembly_rates": ASSEMBLY_PRODUCTION_RATES,
        "reject_rate": REJECT_RATE,
        "bom": BOM,
        "raw_materials_per_part": RAW_MATERIALS_PER_PART,
        "setup_time": SETUP_TIME_HOURS,
    },
    "logistics": {
        "lead_times": LEAD_TIMES,
        "expedited_shipping_cost": EXPEDITED_SHIPPING_COST,
    },
    "workforce": {
        "efficiency": OPERATOR_EFFICIENCY,
        "costs": WORKFORCE_COSTS,
    },
    "equipment": {
        "repair": MACHINE_REPAIR,
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
