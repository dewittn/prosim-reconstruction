"""Tests for decision validation."""

import pytest

from prosim.engine.validation import (
    ValidationError,
    ValidationResult,
    validate_decisions,
    validate_decisions_with_messages,
)
from prosim.models.company import Company
from prosim.models.decisions import Decisions, MachineDecision, PartOrders


@pytest.fixture
def sample_company():
    """Create a sample company for testing."""
    return Company.create_new(company_id=1, name="Test Company")


@pytest.fixture
def valid_decisions():
    """Create valid decisions for week 1."""
    return Decisions(
        week=1,
        company_id=1,
        quality_budget=500.0,
        maintenance_budget=300.0,
        raw_materials_regular=1000.0,
        raw_materials_expedited=0.0,
        part_orders=PartOrders(x_prime=0.0, y_prime=0.0, z_prime=0.0),
        machine_decisions=[
            MachineDecision(machine_id=i, send_for_training=False, part_type=1, scheduled_hours=40.0)
            for i in range(1, 10)
        ],
    )


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_success_result(self):
        """Test creating a success result."""
        result = ValidationResult.success()
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_failure_result(self):
        """Test creating a failure result."""
        errors = [ValidationError(field="test", message="Test error")]
        result = ValidationResult.failure(errors)
        assert result.valid is False
        assert len(result.errors) == 1

    def test_add_error(self):
        """Test adding an error."""
        result = ValidationResult(valid=True)
        result.add_error(ValidationError(field="test", message="Test error"))
        assert result.valid is False
        assert len(result.errors) == 1

    def test_add_warning(self):
        """Test adding a warning doesn't affect validity."""
        result = ValidationResult(valid=True)
        result.add_warning(ValidationError(field="test", message="Test warning"))
        assert result.valid is True
        assert len(result.warnings) == 1

    def test_merge_results(self):
        """Test merging validation results."""
        result1 = ValidationResult(valid=True)
        result1.add_warning(ValidationError(field="warn1", message="Warning 1"))

        result2 = ValidationResult(valid=True)
        result2.add_error(ValidationError(field="err1", message="Error 1"))

        result1.merge(result2)
        assert result1.valid is False
        assert len(result1.warnings) == 1
        assert len(result1.errors) == 1


class TestValidateDecisions:
    """Tests for validate_decisions function."""

    def test_valid_decisions(self, sample_company, valid_decisions):
        """Test validation of valid decisions."""
        result = validate_decisions(valid_decisions, sample_company)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_wrong_week(self, sample_company, valid_decisions):
        """Test validation fails for wrong week."""
        wrong_week = valid_decisions.model_copy(update={"week": 5})
        result = validate_decisions(wrong_week, sample_company)
        assert result.valid is False
        assert any("week" in e.field for e in result.errors)

    def test_wrong_company_id(self, sample_company, valid_decisions):
        """Test validation fails for wrong company ID."""
        wrong_company = valid_decisions.model_copy(update={"company_id": 99})
        result = validate_decisions(wrong_company, sample_company)
        assert result.valid is False
        assert any("company_id" in e.field for e in result.errors)

    def test_negative_quality_budget(self, sample_company, valid_decisions):
        """Test validation fails for negative quality budget."""
        negative_budget = valid_decisions.model_copy(update={"quality_budget": -100.0})
        result = validate_decisions(negative_budget, sample_company)
        assert result.valid is False
        assert any("quality_budget" in e.field for e in result.errors)

    def test_negative_maintenance_budget(self, sample_company, valid_decisions):
        """Test validation fails for negative maintenance budget."""
        negative_budget = valid_decisions.model_copy(update={"maintenance_budget": -100.0})
        result = validate_decisions(negative_budget, sample_company)
        assert result.valid is False
        assert any("maintenance_budget" in e.field for e in result.errors)

    def test_high_budget_warning(self, sample_company, valid_decisions):
        """Test warning for unusually high budgets."""
        high_budget = valid_decisions.model_copy(update={"quality_budget": 15000.0})
        result = validate_decisions(high_budget, sample_company)
        assert result.valid is True  # Still valid, just a warning
        assert any("quality_budget" in w.field for w in result.warnings)

    def test_negative_raw_materials(self, sample_company, valid_decisions):
        """Test validation fails for negative raw materials orders."""
        negative_rm = valid_decisions.model_copy(update={"raw_materials_regular": -100.0})
        result = validate_decisions(negative_rm, sample_company)
        assert result.valid is False

    def test_expedited_only_warning(self, sample_company, valid_decisions):
        """Test warning when using expedited orders only."""
        expedited_only = valid_decisions.model_copy(
            update={
                "raw_materials_regular": 0.0,
                "raw_materials_expedited": 500.0,
            }
        )
        result = validate_decisions(expedited_only, sample_company)
        assert result.valid is True
        assert any("expedited" in w.field for w in result.warnings)

    def test_zero_parts_order(self, sample_company, valid_decisions):
        """Test validation accepts zero parts orders."""
        zero_parts = valid_decisions.model_copy(
            update={
                "part_orders": PartOrders(x_prime=0.0, y_prime=0.0, z_prime=0.0)
            }
        )
        result = validate_decisions(zero_parts, sample_company)
        # Zero is valid, no errors
        assert len([e for e in result.errors if "part_orders" in e.field]) == 0

    def test_large_parts_order_warning(self, sample_company, valid_decisions):
        """Test warning for large parts orders."""
        large_parts = valid_decisions.model_copy(
            update={
                "part_orders": PartOrders(x_prime=500.0, y_prime=500.0, z_prime=500.0)
            }
        )
        result = validate_decisions(large_parts, sample_company)
        assert result.valid is True
        assert any("part_orders" in w.field for w in result.warnings)

    def test_maximum_hours(self, sample_company):
        """Test validation accepts maximum scheduled hours (50)."""
        decisions = Decisions(
            week=1,
            company_id=1,
            quality_budget=0.0,
            maintenance_budget=0.0,
            machine_decisions=[
                MachineDecision(
                    machine_id=i,
                    send_for_training=False,
                    part_type=1,
                    scheduled_hours=50.0,  # Maximum valid hours
                )
                for i in range(1, 10)
            ],
        )
        result = validate_decisions(decisions, sample_company)
        # Maximum hours are valid
        assert len([e for e in result.errors if "hours" in e.field]) == 0

    def test_training_many_operators_warning(self, sample_company):
        """Test warning when training too many operators at once."""
        decisions = Decisions(
            week=1,
            company_id=1,
            quality_budget=0.0,
            maintenance_budget=0.0,
            machine_decisions=[
                MachineDecision(
                    machine_id=i,
                    send_for_training=(i <= 4),  # Train 4 operators
                    part_type=1,
                    scheduled_hours=0.0 if i <= 4 else 40.0,
                )
                for i in range(1, 10)
            ],
        )
        result = validate_decisions(decisions, sample_company)
        assert result.valid is True
        assert any("training" in w.message.lower() for w in result.warnings)

    def test_parts_only_production_warning(self, sample_company):
        """Test warning when only producing parts with no assembly."""
        decisions = Decisions(
            week=1,
            company_id=1,
            quality_budget=0.0,
            maintenance_budget=0.0,
            machine_decisions=[
                MachineDecision(
                    machine_id=i,
                    send_for_training=False,
                    part_type=1,
                    scheduled_hours=40.0 if i <= 4 else 0.0,  # Only parts production
                )
                for i in range(1, 10)
            ],
        )
        result = validate_decisions(decisions, sample_company)
        assert result.valid is True
        assert any("assembly" in w.message.lower() for w in result.warnings)

    def test_strict_mode_treats_warnings_as_errors(self, sample_company, valid_decisions):
        """Test that strict mode converts warnings to errors."""
        high_budget = valid_decisions.model_copy(update={"quality_budget": 15000.0})

        # Normal mode - valid with warning
        normal_result = validate_decisions(high_budget, sample_company, strict=False)
        assert normal_result.valid is True
        assert len(normal_result.warnings) > 0

        # Strict mode - invalid
        strict_result = validate_decisions(high_budget, sample_company, strict=True)
        assert strict_result.valid is False
        assert len(strict_result.errors) > 0


class TestValidateDecisionsWithMessages:
    """Tests for validate_decisions_with_messages convenience function."""

    def test_valid_decisions_returns_no_messages(self, sample_company, valid_decisions):
        """Test that valid decisions return no messages."""
        valid, messages = validate_decisions_with_messages(valid_decisions, sample_company)
        assert valid is True
        # May have warnings, but no errors
        errors = [m for m in messages if "[ERROR]" in m]
        assert len(errors) == 0

    def test_invalid_decisions_returns_error_messages(self, sample_company, valid_decisions):
        """Test that invalid decisions return error messages."""
        wrong_week = valid_decisions.model_copy(update={"week": 5})
        valid, messages = validate_decisions_with_messages(wrong_week, sample_company)
        assert valid is False
        errors = [m for m in messages if "[ERROR]" in m]
        assert len(errors) > 0

    def test_warnings_returned_as_messages(self, sample_company, valid_decisions):
        """Test that warnings are included in messages."""
        high_budget = valid_decisions.model_copy(update={"quality_budget": 15000.0})
        valid, messages = validate_decisions_with_messages(high_budget, sample_company)
        assert valid is True
        warnings = [m for m in messages if "[WARNING]" in m]
        assert len(warnings) > 0


class TestValidationError:
    """Tests for ValidationError class."""

    def test_error_str_basic(self):
        """Test basic error string representation."""
        error = ValidationError(field="test", message="Test message")
        assert "test" in str(error)
        assert "Test message" in str(error)

    def test_error_str_with_value(self):
        """Test error string with value."""
        error = ValidationError(field="test", message="Test message", value="123")
        assert "123" in str(error)

    def test_error_str_with_suggestion(self):
        """Test error string with suggestion."""
        error = ValidationError(
            field="test",
            message="Test message",
            suggestion="Try this instead",
        )
        assert "Try this instead" in str(error)


class TestIntegration:
    """Integration tests for validation."""

    def test_full_validation_workflow(self, sample_company):
        """Test complete validation workflow."""
        # Create decisions with multiple issues
        decisions = Decisions(
            week=1,
            company_id=1,
            quality_budget=15000.0,  # Warning: high budget
            maintenance_budget=0.0,
            raw_materials_expedited=500.0,  # Warning: using expedited
            machine_decisions=[
                MachineDecision(
                    machine_id=i,
                    send_for_training=False,
                    part_type=1,
                    scheduled_hours=40.0,
                )
                for i in range(1, 10)
            ],
        )

        result = validate_decisions(decisions, sample_company)

        # Should be valid but with warnings
        assert result.valid is True
        assert len(result.warnings) >= 2  # At least high budget and expedited warnings

        # Get messages
        valid, messages = validate_decisions_with_messages(decisions, sample_company)
        assert valid is True
        assert len(messages) >= 2
