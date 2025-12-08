"""
Unit tests for PROSIM data models.
"""

import pytest
from prosim.models import (
    # Inventory
    Inventory,
    PartsInventory,
    ProductsInventory,
    RawMaterialsInventory,
    # Operators
    Department,
    Operator,
    TrainingStatus,
    Workforce,
    # Machines
    Machine,
    MachineFloor,
    # Orders
    DemandSchedule,
    Order,
    OrderBook,
    OrderType,
    # Decisions
    Decisions,
    MachineDecision,
    PartOrders,
    # Report
    CostReport,
    ProductCosts,
    WeeklyReport,
    # Company
    Company,
    CompanyConfig,
    GameState,
)


class TestInventory:
    """Tests for inventory models."""

    def test_raw_materials_ending_calculation(self) -> None:
        inv = RawMaterialsInventory(
            beginning=1000.0,
            orders_received=500.0,
            used_in_production=300.0,
        )
        assert inv.ending == 1200.0

    def test_raw_materials_ending_never_negative(self) -> None:
        inv = RawMaterialsInventory(
            beginning=100.0,
            orders_received=0.0,
            used_in_production=500.0,
        )
        assert inv.ending == 0.0

    def test_raw_materials_advance_week(self) -> None:
        inv = RawMaterialsInventory(
            beginning=1000.0,
            orders_received=500.0,
            used_in_production=300.0,
        )
        next_week = inv.advance_week()
        assert next_week.beginning == 1200.0
        assert next_week.orders_received == 0.0
        assert next_week.used_in_production == 0.0

    def test_parts_inventory_ending_calculation(self) -> None:
        inv = PartsInventory(
            part_type="X'",
            beginning=500.0,
            orders_received=100.0,
            production=300.0,
            used_in_assembly=200.0,
        )
        assert inv.ending == 700.0

    def test_products_inventory_ending_calculation(self) -> None:
        inv = ProductsInventory(
            product_type="X",
            beginning=100.0,
            production=500.0,
            demand_fulfilled=400.0,
        )
        assert inv.ending == 200.0

    def test_inventory_advance_week(self) -> None:
        inv = Inventory()
        inv.raw_materials = RawMaterialsInventory(
            beginning=1000.0,
            orders_received=0.0,
            used_in_production=100.0,
        )
        next_week = inv.advance_week()
        assert next_week.raw_materials.beginning == 900.0


class TestOperators:
    """Tests for operator models."""

    def test_operator_efficiency_trained(self) -> None:
        op = Operator(operator_id=1, training_status=TrainingStatus.TRAINED)
        assert op.is_trained
        assert op.efficiency_range == (0.95, 1.00)

    def test_operator_efficiency_untrained(self) -> None:
        op = Operator(operator_id=1, training_status=TrainingStatus.UNTRAINED)
        assert not op.is_trained
        assert op.efficiency_range == (0.60, 0.90)

    def test_operator_efficiency_in_training(self) -> None:
        op = Operator(operator_id=1, training_status=TrainingStatus.TRAINING)
        assert op.efficiency_range == (0.0, 0.0)

    def test_operator_termination_threshold(self) -> None:
        op = Operator(operator_id=1, consecutive_weeks_unscheduled=1)
        assert not op.should_be_terminated
        op = Operator(operator_id=1, consecutive_weeks_unscheduled=2)
        assert op.should_be_terminated

    def test_workforce_hire_operator(self) -> None:
        workforce = Workforce.create_initial(9, 0)
        assert len(workforce.operators) == 9

        workforce, new_op = workforce.hire_operator(trained=True)
        assert len(workforce.operators) == 10
        assert new_op.operator_id == 10
        assert new_op.is_trained
        assert new_op.is_new_hire

    def test_workforce_terminate_operator(self) -> None:
        workforce = Workforce.create_initial(9, 0)
        workforce = workforce.terminate_operator(1)
        assert len(workforce.operators) == 8
        assert 1 not in workforce.operators

    def test_workforce_count_by_status(self) -> None:
        workforce = Workforce.create_initial(9, 3)
        counts = workforce.count_by_status()
        assert counts[TrainingStatus.TRAINED] == 3
        assert counts[TrainingStatus.UNTRAINED] == 6


class TestMachines:
    """Tests for machine models."""

    def test_machine_floor_default_creation(self) -> None:
        floor = MachineFloor.create_default()
        assert len(floor.machines) == 9
        assert len(floor.parts_machines) == 4
        assert len(floor.assembly_machines) == 5

    def test_machine_department_assignment(self) -> None:
        floor = MachineFloor.create_default()
        for m in floor.parts_machines:
            assert m.department == Department.PARTS
        for m in floor.assembly_machines:
            assert m.department == Department.ASSEMBLY

    def test_machine_assignment(self) -> None:
        machine = Machine(machine_id=1, department=Department.PARTS)
        assert not machine.is_assigned

        machine = machine.assign(
            operator_id=1,
            part_type="X'",
            scheduled_hours=40.0,
        )
        assert machine.is_assigned
        assert machine.assignment is not None
        assert machine.assignment.operator_id == 1
        assert machine.assignment.part_type == "X'"
        assert machine.assignment.scheduled_hours == 40.0

    def test_machine_setup_time(self) -> None:
        machine = Machine(machine_id=1, department=Department.PARTS, last_part_type="X'")
        assert machine.calculate_setup_time("X'") == 0.0
        assert machine.calculate_setup_time("Y'") == 2.0


class TestOrders:
    """Tests for order models."""

    def test_order_book_place_order(self) -> None:
        book = OrderBook()
        book, order = book.place_order(
            OrderType.RAW_MATERIALS_REGULAR,
            amount=1000.0,
            current_week=1,
        )
        assert len(book.orders) == 1
        assert order.week_placed == 1
        assert order.week_due == 4  # 3 week lead time
        assert order.amount == 1000.0

    def test_order_book_expedited_lead_time(self) -> None:
        book = OrderBook()
        book, order = book.place_order(
            OrderType.RAW_MATERIALS_EXPEDITED,
            amount=500.0,
            current_week=1,
        )
        assert order.week_due == 2  # 1 week lead time

    def test_order_book_receive_orders(self) -> None:
        book = OrderBook()
        book, _ = book.place_order(OrderType.RAW_MATERIALS_REGULAR, 1000.0, 1)
        book, _ = book.place_order(OrderType.RAW_MATERIALS_EXPEDITED, 500.0, 1)

        book, received = book.receive_orders(current_week=2)
        assert len(received) == 1
        assert received[0].amount == 500.0
        assert len(book.orders) == 1

    def test_demand_schedule_shipping_week(self) -> None:
        schedule = DemandSchedule(shipping_frequency=4)
        assert schedule.is_shipping_week(4)
        assert schedule.is_shipping_week(8)
        assert not schedule.is_shipping_week(3)
        assert schedule.next_shipping_week(1) == 4
        assert schedule.next_shipping_week(4) == 4
        assert schedule.next_shipping_week(5) == 8


class TestDecisions:
    """Tests for decisions models."""

    def test_machine_decision_train_flag(self) -> None:
        # 0 in DECS file means "send for training"
        md = MachineDecision(
            machine_id=1,
            send_for_training=0,  # type: ignore[arg-type] - testing validator
            part_type=1,
            scheduled_hours=40.0,
        )
        assert md.send_for_training is True

        # 1 in DECS file means "already trained/working"
        md = MachineDecision(
            machine_id=1,
            send_for_training=1,  # type: ignore[arg-type] - testing validator
            part_type=1,
            scheduled_hours=40.0,
        )
        assert md.send_for_training is False

    def test_part_orders_from_list(self) -> None:
        orders = PartOrders.from_list([600.0, 500.0, 400.0])
        assert orders.x_prime == 600.0
        assert orders.y_prime == 500.0
        assert orders.z_prime == 400.0

    def test_decisions_default_creation(self) -> None:
        decisions = Decisions.create_default(week=1, company_id=1)
        assert decisions.week == 1
        assert decisions.company_id == 1
        assert len(decisions.machine_decisions) == 9

    def test_decisions_department_filtering(self) -> None:
        decisions = Decisions.create_default(week=1)
        assert len(decisions.parts_department_decisions) == 4
        assert len(decisions.assembly_department_decisions) == 5


class TestReport:
    """Tests for report models."""

    def test_product_costs_subtotal(self) -> None:
        costs = ProductCosts(
            product_type="X",
            labor=1200.0,
            machine_setup=80.0,
            raw_materials=3726.0,
            purchased_parts=2550.0,
            equipment_usage=2400.0,
        )
        assert costs.subtotal == 9956.0

    def test_cost_report_total(self) -> None:
        report = CostReport()
        report.x_costs = ProductCosts(product_type="X", labor=1000.0)
        report.y_costs = ProductCosts(product_type="Y", labor=500.0)
        report.z_costs = ProductCosts(product_type="Z", labor=800.0)
        assert report.product_subtotal == 2300.0

    def test_weekly_report_creation(self) -> None:
        report = WeeklyReport(week=1, company_id=1)
        assert report.week == 1
        assert report.weekly_costs.total_costs == 0.0


class TestCompany:
    """Tests for company models."""

    def test_company_creation(self) -> None:
        company = Company.create_new(company_id=1, name="Test Corp")
        assert company.company_id == 1
        assert company.name == "Test Corp"
        assert company.current_week == 1
        assert len(company.machines.machines) == 9
        assert len(company.workforce.operators) == 9

    def test_company_custom_config(self) -> None:
        config = CompanyConfig(
            num_parts_machines=3,
            num_assembly_machines=4,
            num_operators=7,
            num_trained_operators=2,
        )
        company = Company.create_new(company_id=1, config=config)
        assert len(company.machines.parts_machines) == 3
        assert len(company.machines.assembly_machines) == 4
        assert len(company.workforce.operators) == 7
        assert len(company.workforce.trained_operators) == 2

    def test_company_advance_week(self) -> None:
        company = Company.create_new(company_id=1)
        company = company.advance_week()
        assert company.current_week == 2

    def test_game_state_single_player(self) -> None:
        game = GameState.create_single_player(
            game_id="test-game",
            company_name="Player Co",
        )
        assert len(game.companies) == 1
        assert game.current_week == 1
        assert game.is_active

    def test_game_state_multiplayer(self) -> None:
        game = GameState.create_multiplayer(
            game_id="test-game",
            num_companies=4,
        )
        assert len(game.companies) == 4
        for i in range(1, 5):
            assert i in game.companies

    def test_game_state_advance_week(self) -> None:
        game = GameState.create_single_player(game_id="test")
        game = game.advance_week()
        assert game.current_week == 2
        assert game.get_company(1) is not None
        assert game.get_company(1).current_week == 2  # type: ignore[union-attr]

    def test_game_state_completion(self) -> None:
        game = GameState.create_single_player(game_id="test", max_weeks=3)
        assert not game.is_complete
        game = game.advance_week()  # week 2
        game = game.advance_week()  # week 3
        game = game.advance_week()  # week 4
        assert game.is_complete
        assert not game.is_active
