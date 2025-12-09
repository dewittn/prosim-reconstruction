"""
Calibration module for PROSIM simulation parameters.

This module provides tools for calibrating simulation parameters based on
analysis of original PROSIM output files. It documents findings from the
original data and provides functions to derive optimal parameter values.

Key Findings from Original Data:
--------------------------------

1. REJECT RATE VARIATION:
   - Week 12: ~11.85% reject rate
   - Week 13: ~15% reject rate
   - Week 14: ~17.8% reject rate (documented in case study)

   The variation strongly suggests reject rate is influenced by quality budget.
   Higher quality budgets likely result in lower reject rates.

2. PRODUCTION RATES:
   Documented rates (from case study):
   - Parts: X'=60, Y'=50, Z'=40 per productive hour
   - Assembly: X=40, Y=30, Z=20 per productive hour

   Observed rates vary due to:
   - Operator efficiency (trained vs untrained)
   - Setup time deductions
   - Raw material constraints (can't produce more than materials allow)

3. OPERATOR EFFICIENCY:
   - Trained operators: 95-100% efficiency (observed: some at 100%)
   - Untrained operators: 60-90% efficiency (observed: 32.1-43.1 productive
     hours out of scheduled, suggesting varying efficiency)

4. COST PARAMETERS (Verified from week1.txt):
   - Labor: $10/hour scheduled
   - Equipment: ~$20/hour scheduled (derived)
   - Machine repair: $400/repair (verified)
   - Hiring: $2,700/new hire (verified)
   - Layoff: $200/week unscheduled (verified)
   - Termination: $400 after 2 weeks (verified)
   - Fixed expense: $1,500/week (verified)
   - Training: $1,000/session (estimated)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from prosim.config.schema import ProsimConfig, get_default_config


@dataclass
class ProductionRateAnalysis:
    """Analysis of production rates from original data."""

    part_type: str
    total_productive_hours: float
    total_gross_production: float
    total_rejects: float
    total_net_production: float
    observed_rate: float  # gross production / productive hours
    expected_rate: float  # from documentation
    rate_ratio: float  # observed / expected
    reject_rate: float


@dataclass
class RejectRateAnalysis:
    """Analysis of reject rates from original data."""

    week: int
    company_id: int
    total_production: float
    total_rejects: float
    reject_rate: float
    quality_budget: Optional[float]
    maintenance_budget: Optional[float]


@dataclass
class CalibrationReport:
    """Complete calibration report from original data analysis."""

    production_analysis: list[ProductionRateAnalysis]
    reject_analysis: list[RejectRateAnalysis]
    efficiency_analysis: dict[str, float]
    cost_analysis: dict[str, float]
    recommended_config_updates: dict[str, any]


def analyze_reject_rate_from_report(
    report,  # WeeklyReport
    quality_budget: Optional[float] = None,
) -> RejectRateAnalysis:
    """Analyze reject rate from a single report.

    Args:
        report: WeeklyReport from original data
        quality_budget: Quality budget if known (from DECS file)

    Returns:
        RejectRateAnalysis with calculated values
    """
    all_production = (
        report.production.parts_department + report.production.assembly_department
    )

    total_production = sum(mp.production for mp in all_production)
    total_rejects = sum(mp.rejects for mp in all_production)

    reject_rate = total_rejects / total_production if total_production > 0 else 0.0

    return RejectRateAnalysis(
        week=report.week,
        company_id=report.company_id,
        total_production=total_production,
        total_rejects=total_rejects,
        reject_rate=reject_rate,
        quality_budget=quality_budget,
        maintenance_budget=None,
    )


def calculate_quality_adjusted_reject_rate(
    base_reject_rate: float,
    quality_budget: float,
    optimal_quality_budget: float = 750.0,
    sensitivity: float = 0.0001,
) -> float:
    """Calculate reject rate adjusted for quality budget.

    This implements a linear model where higher quality budgets
    reduce the reject rate. Based on observed data:
    - Week 12 (~$750 budget): ~11.85% reject rate
    - Week 14 (varying budget): ~17.8% reject rate

    Args:
        base_reject_rate: Base reject rate (at optimal budget)
        quality_budget: Current quality planning budget
        optimal_quality_budget: Quality budget at which base rate applies
        sensitivity: How much reject rate changes per dollar difference

    Returns:
        Adjusted reject rate
    """
    budget_diff = optimal_quality_budget - quality_budget
    adjustment = budget_diff * sensitivity
    adjusted_rate = base_reject_rate + adjustment

    # Clamp to reasonable bounds
    return max(0.05, min(0.30, adjusted_rate))


def analyze_production_rates_from_report(
    report,  # WeeklyReport
    config: Optional[ProsimConfig] = None,
) -> list[ProductionRateAnalysis]:
    """Analyze production rates from a single report.

    Args:
        report: WeeklyReport from original data
        config: Configuration with expected rates

    Returns:
        List of ProductionRateAnalysis, one per part/product type
    """
    config = config or get_default_config()

    # Aggregate by part type
    by_type: dict[str, dict] = {}

    for mp in report.production.parts_department:
        part_type = mp.part_type
        if part_type not in by_type:
            by_type[part_type] = {
                "productive_hours": 0.0,
                "production": 0.0,  # This is gross
                "rejects": 0.0,
                "expected_rate": config.production.parts_rates.get(
                    part_type, 0
                ),
            }
        by_type[part_type]["productive_hours"] += mp.productive_hours
        by_type[part_type]["production"] += mp.production
        by_type[part_type]["rejects"] += mp.rejects

    for mp in report.production.assembly_department:
        part_type = mp.part_type
        if part_type not in by_type:
            by_type[part_type] = {
                "productive_hours": 0.0,
                "production": 0.0,
                "rejects": 0.0,
                "expected_rate": config.production.assembly_rates.get(
                    part_type, 0
                ),
            }
        by_type[part_type]["productive_hours"] += mp.productive_hours
        by_type[part_type]["production"] += mp.production
        by_type[part_type]["rejects"] += mp.rejects

    results = []
    for part_type, data in by_type.items():
        productive_hours = data["productive_hours"]
        gross = data["production"]
        rejects = data["rejects"]
        net = gross - rejects

        observed_rate = gross / productive_hours if productive_hours > 0 else 0.0
        expected_rate = float(data["expected_rate"])
        rate_ratio = observed_rate / expected_rate if expected_rate > 0 else 0.0
        reject_rate = rejects / gross if gross > 0 else 0.0

        results.append(ProductionRateAnalysis(
            part_type=part_type,
            total_productive_hours=productive_hours,
            total_gross_production=gross,
            total_rejects=rejects,
            total_net_production=net,
            observed_rate=observed_rate,
            expected_rate=expected_rate,
            rate_ratio=rate_ratio,
            reject_rate=reject_rate,
        ))

    return results


def derive_equipment_rate_from_costs(
    total_equipment_cost: float,
    total_scheduled_hours: float,
) -> float:
    """Derive equipment usage rate from cost data.

    From week1.txt:
    - Equipment X: $2,400 (3 machines * 40 hrs implies $20/hr)
    - Equipment Y: $1,600 (2 machines * 40 hrs implies $20/hr)
    - Equipment Z: $4,000 (5 machines * 40 hrs implies $20/hr)

    Args:
        total_equipment_cost: Total equipment usage cost
        total_scheduled_hours: Total scheduled hours across all machines

    Returns:
        Equipment cost per scheduled hour
    """
    if total_scheduled_hours == 0:
        return 0.0
    return total_equipment_cost / total_scheduled_hours


def derive_raw_material_cost_per_unit(
    total_rm_cost: float,
    total_rm_consumed: float,
) -> float:
    """Derive raw material cost per unit consumed.

    From week1.txt:
    - Raw Materials total: $12,451
    - Raw Materials used: 11,099 units
    - Cost per unit: $12,451 / 11,099 ≈ $1.12/unit

    Args:
        total_rm_cost: Total raw material cost
        total_rm_consumed: Total raw materials consumed

    Returns:
        Cost per raw material unit
    """
    if total_rm_consumed == 0:
        return 0.0
    return total_rm_cost / total_rm_consumed


def derive_carrying_cost_rates(
    parts_carrying_cost: float,
    products_carrying_cost: float,
    avg_parts_inventory: float,
    avg_products_inventory: float,
) -> tuple[float, float]:
    """Derive carrying cost rates from cost data.

    Args:
        parts_carrying_cost: Total parts carrying cost
        products_carrying_cost: Total products carrying cost
        avg_parts_inventory: Average parts inventory during period
        avg_products_inventory: Average products inventory during period

    Returns:
        Tuple of (parts_rate, products_rate) per unit per week
    """
    parts_rate = parts_carrying_cost / avg_parts_inventory if avg_parts_inventory > 0 else 0.0
    products_rate = products_carrying_cost / avg_products_inventory if avg_products_inventory > 0 else 0.0
    return parts_rate, products_rate


def create_calibrated_config(
    base_config: Optional[ProsimConfig] = None,
    quality_budget: float = 750.0,
    use_dynamic_reject_rate: bool = True,
) -> ProsimConfig:
    """Create a calibrated configuration based on analysis.

    Args:
        base_config: Base configuration to modify
        quality_budget: Expected quality budget for reject rate calculation
        use_dynamic_reject_rate: If True, adjust reject rate for quality budget

    Returns:
        Calibrated ProsimConfig
    """
    config = base_config or get_default_config()

    # Apply calibrated values based on analysis
    updates = {}

    if use_dynamic_reject_rate:
        # Use the base reject rate of ~11.85% at $750 quality budget
        # Adjust based on actual quality budget
        base_rate = 0.1185
        adjusted_rate = calculate_quality_adjusted_reject_rate(
            base_rate, quality_budget, optimal_quality_budget=750.0
        )
        updates["production"] = {"reject_rate": adjusted_rate}

    if updates:
        return config.merge(updates)
    return config


# Known calibration values from original data analysis
CALIBRATION_DATA = {
    "reject_rates_by_week": {
        12: 0.1185,  # ~11.85%
        13: 0.15,    # ~15%
        14: 0.178,   # ~17.8%
    },
    "quality_budget_reject_correlation": {
        # Higher quality budget -> lower reject rate
        "base_rate_at_750": 0.1185,
        "sensitivity": 0.0001,  # Rate change per dollar
    },
    "verified_costs": {
        "labor_hourly": 10.0,
        "equipment_hourly": 20.0,  # Derived from week1.txt
        "repair_per_incident": 400.0,
        "hiring_per_worker": 2700.0,
        "layoff_per_week": 200.0,
        "termination": 400.0,
        "fixed_expense": 1500.0,
        "training_per_worker": 1000.0,
    },
    "production_rates": {
        "parts": {"X'": 60, "Y'": 50, "Z'": 40},
        "assembly": {"X": 40, "Y": 30, "Z": 20},
    },
    "efficiency_ranges": {
        # Default efficiency ranges from case study
        "trained": {"min": 0.95, "max": 1.00},
        "untrained": {"min": 0.60, "max": 0.90},
    },
    "observed_efficiencies": {
        # Observed from week1.txt production data
        # Parts dept: 92.5%, 83.25%, 92.5%, 92.5% (showing untrained variation)
        # Assembly dept: 100%, 100%, 100%, 100%, 90% (mostly trained)
        "week1_parts_department": [0.925, 0.8325, 0.925, 0.925],
        "week1_assembly_department": [1.0, 1.0, 1.0, 1.0, 0.90],
        "min_observed_week1": 0.8325,
        "max_observed_week1": 1.00,
        # Week 14 shows lower efficiency (0.58), suggesting new hires or other factors
        "min_observed_week14": 0.58,
        "notes": (
            "Observed efficiencies vary by week. Week 1 shows 83-100% range, "
            "while Week 14 shows efficiency as low as 58%. This suggests that "
            "new/very untrained operators can fall below the documented 60% "
            "minimum. The efficiency model should accommodate this variance."
        ),
    },
}


def analyze_operator_efficiency_from_report(
    report,  # WeeklyReport
) -> dict[str, list[float]]:
    """Analyze operator efficiency from a report.

    Args:
        report: WeeklyReport from original data

    Returns:
        Dict with 'parts' and 'assembly' efficiency lists
    """
    efficiencies: dict[str, list[float]] = {
        "parts": [],
        "assembly": [],
    }

    for mp in report.production.parts_department:
        if mp.scheduled_hours > 0:
            eff = mp.productive_hours / mp.scheduled_hours
            efficiencies["parts"].append(eff)

    for mp in report.production.assembly_department:
        if mp.scheduled_hours > 0:
            eff = mp.productive_hours / mp.scheduled_hours
            efficiencies["assembly"].append(eff)

    return efficiencies


def infer_training_status_from_efficiency(
    efficiency: float,
    trained_threshold: float = 0.95,
) -> str:
    """Infer training status from observed efficiency.

    Args:
        efficiency: Observed efficiency ratio (0.0-1.0)
        trained_threshold: Threshold above which operator is likely trained

    Returns:
        'trained' or 'untrained'
    """
    if efficiency >= trained_threshold:
        return "trained"
    return "untrained"


def calculate_efficiency_statistics(
    efficiencies: list[float],
) -> dict[str, float]:
    """Calculate statistics for a list of efficiency values.

    Args:
        efficiencies: List of efficiency values

    Returns:
        Dict with min, max, mean, trained_count, untrained_count
    """
    if not efficiencies:
        return {
            "min": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "trained_count": 0,
            "untrained_count": 0,
        }

    trained_count = sum(1 for e in efficiencies if e >= 0.95)
    untrained_count = len(efficiencies) - trained_count

    return {
        "min": min(efficiencies),
        "max": max(efficiencies),
        "mean": sum(efficiencies) / len(efficiencies),
        "trained_count": trained_count,
        "untrained_count": untrained_count,
    }


def get_calibrated_reject_rate(quality_budget: float) -> float:
    """Get calibrated reject rate based on quality budget.

    Uses the observed correlation between quality budget and reject rate
    from original data analysis.

    Args:
        quality_budget: Quality planning budget

    Returns:
        Calibrated reject rate
    """
    data = CALIBRATION_DATA["quality_budget_reject_correlation"]
    return calculate_quality_adjusted_reject_rate(
        base_reject_rate=data["base_rate_at_750"],
        quality_budget=quality_budget,
        optimal_quality_budget=750.0,
        sensitivity=data["sensitivity"],
    )


# ==============================================================================
# COST PARAMETER CALIBRATION
# ==============================================================================


def derive_labor_rate_from_report(
    report,  # WeeklyReport
) -> float:
    """Derive labor rate from report cost data.

    From week1.txt: Labor = $3,600 for 9 machines * 40 hours = $10/hour

    Args:
        report: WeeklyReport from original data

    Returns:
        Derived labor cost per hour
    """
    total_labor = (
        report.weekly_costs.x_costs.labor
        + report.weekly_costs.y_costs.labor
        + report.weekly_costs.z_costs.labor
    )

    # Get total scheduled hours
    total_hours = 0.0
    for mp in report.production.parts_department:
        total_hours += mp.scheduled_hours
    for mp in report.production.assembly_department:
        total_hours += mp.scheduled_hours

    if total_hours == 0:
        return 0.0

    return total_labor / total_hours


def derive_cost_rates_from_report(
    report,  # WeeklyReport
) -> dict[str, float]:
    """Derive all cost rates from a report.

    Args:
        report: WeeklyReport from original data

    Returns:
        Dict with derived cost rates
    """
    wc = report.weekly_costs

    # Total scheduled hours
    total_hours = 0.0
    for mp in report.production.parts_department:
        total_hours += mp.scheduled_hours
    for mp in report.production.assembly_department:
        total_hours += mp.scheduled_hours

    # Total production for weighted averages
    total_production = sum(
        mp.production for mp in
        report.production.parts_department + report.production.assembly_department
    )

    # Raw materials
    rm = report.inventory.raw_materials
    rm_cost = wc.x_costs.raw_materials + wc.y_costs.raw_materials + wc.z_costs.raw_materials
    rm_rate = rm_cost / rm.used_in_production if rm.used_in_production > 0 else 0.0

    return {
        "labor_hourly": (wc.x_costs.labor + wc.y_costs.labor + wc.z_costs.labor) / total_hours if total_hours > 0 else 0.0,
        "equipment_hourly": (wc.x_costs.equipment_usage + wc.y_costs.equipment_usage + wc.z_costs.equipment_usage) / total_hours if total_hours > 0 else 0.0,
        "raw_materials_per_unit": rm_rate,
        "fixed_expense": wc.overhead.fixed_expense,
        "quality_planning": wc.overhead.quality_planning,
        "plant_maintenance": wc.overhead.plant_maintenance,
    }


# ==============================================================================
# STOCHASTIC ELEMENT HANDLING
# ==============================================================================


def estimate_machine_repair_probability_from_reports(
    reports: list,  # list[WeeklyReport]
) -> float:
    """Estimate machine repair probability from multiple reports.

    Machine repairs are stochastic events. By analyzing multiple weeks,
    we can estimate the probability of a repair occurring.

    From case study: ~10-15% per machine per week observed

    Args:
        reports: List of WeeklyReport objects

    Returns:
        Estimated repair probability per machine per week
    """
    total_repairs = 0
    total_machine_weeks = 0

    for report in reports:
        # Count repairs (each $400 cost = 1 repair)
        repair_cost = (
            report.weekly_costs.x_costs.machine_repair
            + report.weekly_costs.y_costs.machine_repair
            + report.weekly_costs.z_costs.machine_repair
        )
        repairs_this_week = repair_cost / 400.0 if repair_cost > 0 else 0.0
        total_repairs += repairs_this_week

        # Count machines active
        machines_active = len(report.production.parts_department) + len(report.production.assembly_department)
        total_machine_weeks += machines_active

    if total_machine_weeks == 0:
        return 0.10  # Default estimate

    return total_repairs / total_machine_weeks


def get_stochastic_config(
    repair_probability: float = 0.10,
    demand_variance_enabled: bool = True,
    random_seed: int | None = None,
) -> dict:
    """Get configuration for stochastic elements.

    Args:
        repair_probability: Probability of machine repair per week (default 10%)
        demand_variance_enabled: Whether demand forecasts have variance
        random_seed: Seed for reproducibility (None = random)

    Returns:
        Dict with stochastic configuration
    """
    return {
        "machine_repair_probability": repair_probability,
        "demand_variance_enabled": demand_variance_enabled,
        "random_seed": random_seed,
    }


# ==============================================================================
# PRODUCTION FORMULA VERIFICATION
# ==============================================================================


def verify_production_formula(
    scheduled_hours: float,
    setup_hours: float,
    efficiency: float,
    production_rate: float,
    reject_rate: float,
) -> dict[str, float]:
    """Verify production formula calculations.

    Implements the documented formula:
        Productive Hours = (Scheduled Hours - Setup Time) * Operator Efficiency
        Gross Production = Productive Hours * Production Rate
        Rejects = Gross Production * Reject Rate
        Net Production = Gross Production - Rejects

    Args:
        scheduled_hours: Scheduled hours for machine
        setup_hours: Setup time (if changing part type)
        efficiency: Operator efficiency (0.0-1.0)
        production_rate: Units per productive hour
        reject_rate: Fraction rejected (0.0-1.0)

    Returns:
        Dict with calculated values for verification
    """
    available_hours = max(0.0, scheduled_hours - setup_hours)
    productive_hours = available_hours * efficiency
    gross_production = productive_hours * production_rate
    rejects = gross_production * reject_rate
    net_production = gross_production - rejects

    return {
        "scheduled_hours": scheduled_hours,
        "setup_hours": setup_hours,
        "available_hours": available_hours,
        "efficiency": efficiency,
        "productive_hours": productive_hours,
        "production_rate": production_rate,
        "gross_production": gross_production,
        "reject_rate": reject_rate,
        "rejects": rejects,
        "net_production": net_production,
    }
