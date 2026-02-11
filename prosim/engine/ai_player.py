"""
AI player decision generation for PROSIM simulation.

Provides three strategy-based AI players that generate Decisions
objects for computer-controlled competitors in teacher mode.

Strategies:
- Conservative: Stability-focused, moderate budgets, gradual training
- Aggressive: Max output, high budgets, heavy ordering, fast training
- Balanced: Demand-responsive, adapts to inventory and forecasts
"""

import math

from prosim.config.schema import ProsimConfig, get_default_config
from prosim.models.company import Company
from prosim.models.decisions import Decisions, MachineDecision, PartOrders

# Default base demand per product per shipping period
_BASE_DEMAND = {"X": 8467.0, "Y": 6973.0, "Z": 5475.0}

# Production rates for reference
_PARTS_RATES = {"X'": 60, "Y'": 50, "Z'": 40}
_ASSEMBLY_RATES = {"X": 40, "Y": 30, "Z": 20}


class AIPlayer:
    """Generates decisions for an AI-controlled company.

    The AI examines current Company state (inventory, workforce,
    demand forecasts, pending orders) and produces a Decisions
    object appropriate for its strategy and the game phase.
    """

    def __init__(
        self,
        strategy: str,
        company: Company,
        config: ProsimConfig | None = None,
    ):
        self.strategy = strategy
        self.company = company
        self.config = config or get_default_config()

    def generate_decisions(self, week: int) -> Decisions:
        """Generate decisions based on strategy and current state."""
        if self.strategy == "conservative":
            return self._conservative(week)
        elif self.strategy == "aggressive":
            return self._aggressive(week)
        else:
            return self._balanced(week)

    # ------------------------------------------------------------------
    # Strategy implementations
    # ------------------------------------------------------------------

    def _conservative(self, week: int) -> Decisions:
        """Stability-focused strategy.

        - Quality budget $850-900 (moderate reject rate)
        - Maintenance budget $600-700
        - Balanced production across products
        - Order raw materials regularly, avoid expedited
        - Train 1 operator per week if untrained remain
        - Standard 40-hour work weeks
        """
        quality_budget = 875.0
        maintenance_budget = 650.0
        hours = 40.0

        # Order raw materials every week (regular only)
        rm_needed = self._estimate_rm_needed(
            hours, reject_rate_at_budget=quality_budget
        )
        rm_on_hand = self.company.inventory.raw_materials.ending
        rm_order = max(0.0, rm_needed * 3 - rm_on_hand)  # 3-week buffer

        # Machine assignments: balanced across products
        machine_decisions = self._balanced_machine_assignments(hours, max_training=1)

        return Decisions(
            week=week,
            company_id=self.company.company_id,
            quality_budget=quality_budget,
            maintenance_budget=maintenance_budget,
            raw_materials_regular=rm_order,
            raw_materials_expedited=0.0,
            part_orders=PartOrders(),
            machine_decisions=machine_decisions,
        )

    def _aggressive(self, week: int) -> Decisions:
        """Max-output strategy.

        - Quality budget $1200+ (low reject rate)
        - Maintenance budget $800
        - Max hours (50/week)
        - Heavy raw material ordering
        - Train all untrained operators immediately
        - Purchase parts when inventory is low
        """
        quality_budget = 1200.0
        maintenance_budget = 800.0
        hours = 50.0

        # Aggressive ordering
        rm_needed = self._estimate_rm_needed(
            hours, reject_rate_at_budget=quality_budget
        )
        rm_on_hand = self.company.inventory.raw_materials.ending
        rm_order = max(0.0, rm_needed * 4 - rm_on_hand)

        # Purchase parts if product inventory is low before shipping
        part_orders = self._calculate_part_orders(hours, shipping_buffer=1.2)

        # Train all untrained operators
        machine_decisions = self._balanced_machine_assignments(
            hours,
            max_training=9,  # Train everyone possible
        )

        return Decisions(
            week=week,
            company_id=self.company.company_id,
            quality_budget=quality_budget,
            maintenance_budget=maintenance_budget,
            raw_materials_regular=rm_order,
            raw_materials_expedited=0.0,
            part_orders=part_orders,
            machine_decisions=machine_decisions,
        )

    def _balanced(self, week: int) -> Decisions:
        """Demand-responsive strategy.

        Adapts production to match demand forecasts.
        - Quality budget $1000 (10% reject rate)
        - Maintenance budget $700
        - Adjust hours based on inventory vs demand
        - Order based on projected shortfall
        - Train 2 operators per week
        """
        quality_budget = 1000.0
        maintenance_budget = 700.0

        # Determine hours based on game phase
        shipping_freq = self.config.simulation.shipping_frequency
        weeks_until_shipping = shipping_freq - ((week - 1) % shipping_freq)

        # Ramp up before shipping, ease off after
        if weeks_until_shipping <= 2:
            hours = 48.0  # Push before shipping
        elif weeks_until_shipping == shipping_freq:
            hours = 38.0  # Just shipped, ease off
        else:
            hours = 42.0  # Normal pace

        # Smart ordering based on inventory
        rm_needed = self._estimate_rm_needed(
            hours, reject_rate_at_budget=quality_budget
        )
        rm_on_hand = self.company.inventory.raw_materials.ending
        rm_pending = self._pending_rm_orders()
        rm_shortfall = rm_needed * 3 - rm_on_hand - rm_pending

        rm_regular = max(0.0, rm_shortfall)
        rm_expedited = 0.0

        # Use expedited only when critically low before shipping
        if rm_on_hand < rm_needed and weeks_until_shipping <= 2:
            rm_expedited = rm_needed - rm_on_hand
            rm_regular = max(0.0, rm_regular - rm_expedited)

        part_orders = self._calculate_part_orders(hours, shipping_buffer=1.0)

        machine_decisions = self._balanced_machine_assignments(hours, max_training=2)

        return Decisions(
            week=week,
            company_id=self.company.company_id,
            quality_budget=quality_budget,
            maintenance_budget=maintenance_budget,
            raw_materials_regular=rm_regular,
            raw_materials_expedited=rm_expedited,
            part_orders=part_orders,
            machine_decisions=machine_decisions,
        )

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _estimate_rm_needed(self, hours: float, reject_rate_at_budget: float) -> float:
        """Estimate raw materials needed per week for parts production."""
        reject_rate = self._reject_rate(reject_rate_at_budget)
        # 4 parts machines, each producing at average rate
        avg_rate = sum(_PARTS_RATES.values()) / len(_PARTS_RATES)
        # Rough estimate: 4 machines * hours * avg_rate * (1 + reject overhead)
        return (
            4 * hours * avg_rate * (1.0 + reject_rate) * 0.5
        )  # 0.5 efficiency estimate

    def _reject_rate(self, quality_budget: float) -> float:
        """Calculate reject rate from quality budget."""
        if quality_budget <= 0:
            return 0.20
        rate = 0.904 - 0.114 * math.log(quality_budget)
        return max(0.015, rate)

    def _pending_rm_orders(self) -> float:
        """Sum pending raw material orders."""
        total = 0.0
        for order in self.company.orders.orders:
            if "raw_materials" in order.order_type.value:
                total += order.amount
        return total

    def _calculate_part_orders(
        self, hours: float, shipping_buffer: float
    ) -> PartOrders:
        """Calculate purchased parts orders based on assembly needs."""
        # Only buy parts if we need them soon
        shipping_freq = self.config.simulation.shipping_frequency
        week = self.company.current_week
        weeks_until_shipping = shipping_freq - ((week - 1) % shipping_freq)

        if weeks_until_shipping > 2:
            return PartOrders()

        # Check if parts inventory is low for upcoming assembly
        parts_inv = self.company.inventory.parts
        x_low = parts_inv.x_prime.ending < hours * _ASSEMBLY_RATES["X"] * 0.3
        y_low = parts_inv.y_prime.ending < hours * _ASSEMBLY_RATES["Y"] * 0.3
        z_low = parts_inv.z_prime.ending < hours * _ASSEMBLY_RATES["Z"] * 0.3

        return PartOrders(
            x_prime=hours * _ASSEMBLY_RATES["X"] * shipping_buffer if x_low else 0.0,
            y_prime=hours * _ASSEMBLY_RATES["Y"] * shipping_buffer if y_low else 0.0,
            z_prime=hours * _ASSEMBLY_RATES["Z"] * shipping_buffer if z_low else 0.0,
        )

    def _balanced_machine_assignments(
        self,
        hours: float,
        max_training: int = 1,
    ) -> list[MachineDecision]:
        """Create machine assignments balanced across product types.

        Parts machines (1-4): Distribute across X', Y', Z'
        Assembly machines (5-9): Distribute across X, Y, Z

        Sends up to max_training untrained operators to training.
        """
        decisions = []
        training_sent = 0
        workforce = self.company.workforce

        for machine_id in range(1, 10):
            operator = workforce.get_operator(machine_id)

            # Check if we should train this operator
            send_training = False
            if (
                operator
                and not operator.is_trained
                and not operator.is_in_training_class
                and training_sent < max_training
            ):
                send_training = True
                training_sent += 1

            # Determine part type: cycle through 1, 2, 3
            if machine_id <= 4:
                # Parts department: distribute X'(1), Y'(2), Z'(3), X'(1)
                part_type = ((machine_id - 1) % 3) + 1
            else:
                # Assembly department: distribute X(1), Y(2), Z(3), X(1), Y(2)
                part_type = ((machine_id - 5) % 3) + 1

            decisions.append(
                MachineDecision(
                    machine_id=machine_id,
                    send_for_training=send_training,
                    part_type=part_type,
                    scheduled_hours=0.0 if send_training else hours,
                )
            )

        return decisions


def create_ai_player(
    strategy: str,
    company: Company,
    config: ProsimConfig | None = None,
) -> AIPlayer:
    """Factory function for creating an AI player.

    Args:
        strategy: One of "conservative", "aggressive", "balanced"
        company: Current company state
        config: Optional game config

    Returns:
        AIPlayer configured with the given strategy
    """
    valid_strategies = ("conservative", "aggressive", "balanced")
    if strategy not in valid_strategies:
        raise ValueError(
            f"Unknown strategy '{strategy}'. Must be one of: {valid_strategies}"
        )
    return AIPlayer(strategy=strategy, company=company, config=config)
