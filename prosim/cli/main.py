"""
PROSIM Command-Line Interface.

A complete CLI for playing the PROSIM production management simulation.
Supports single-player mode with save/load functionality.
"""

import sys
import uuid
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from prosim import __version__
from prosim.config.schema import ProsimConfig, get_default_config
from prosim.engine.simulation import Simulation
from prosim.i18n import t, load_locale
from prosim.engine.validation import validate_decisions
from prosim.io import (
    LoadError,
    SaveError,
    autosave,
    delete_save,
    has_autosave,
    list_saves,
    load_autosave,
    load_game,
    parse_decs,
    save_game,
    write_rept_human_readable,
)
from prosim.models.company import Company, GameState
from prosim.models.decisions import Decisions, MachineDecision, PartOrders
from prosim.models.report import WeeklyReport

console = Console()


# =============================================================================
# Main CLI Group
# =============================================================================


@click.group()
@click.version_option(version=__version__, prog_name="PROSIM")
@click.option(
    "--lang",
    "-l",
    default="en",
    help="Language code (e.g., 'en', 'es')",
)
def cli(lang: str) -> None:
    """
    PROSIM - A Production Management Simulation

    A reconstruction of the 1968 PROSIM simulation game for educational use.
    """
    load_locale(lang)


# =============================================================================
# Game Commands
# =============================================================================


@cli.command()
@click.option("--name", "-n", prompt="Company name", help="Your company name")
@click.option("--weeks", "-w", default=15, help="Maximum simulation weeks")
@click.option("--seed", "-s", type=int, default=None, help="Random seed for reproducibility")
@click.option("--slot", type=int, default=None, help="Save slot to use (auto-saves to this slot)")
def new(name: str, weeks: int, seed: Optional[int], slot: Optional[int]) -> None:
    """Start a new game."""
    console.print()
    console.print(Panel.fit(
        "[bold blue]PROSIM[/bold blue]\n[dim]Production Management Simulation[/dim]",
        border_style="blue",
    ))
    console.print()

    # Create game state
    game_id = str(uuid.uuid4())[:8]
    game_state = GameState.create_single_player(
        game_id=game_id,
        company_name=name,
        max_weeks=weeks,
        random_seed=seed,
    )

    console.print(f"[green]Created new game:[/green] {name}")
    console.print(f"  Game ID: {game_id}")
    console.print(f"  Max Weeks: {weeks}")
    if seed:
        console.print(f"  Random Seed: {seed}")
    console.print()

    # Save if slot specified
    if slot:
        try:
            save_game(game_state, slot)
            console.print(f"[green]Game saved to slot {slot}[/green]")
        except SaveError as e:
            console.print(f"[red]Failed to save: {e}[/red]")

    # Start interactive mode
    _play_game(game_state, slot)


@cli.command()
@click.argument("slot", type=int, required=False)
@click.option("--file", "-f", type=click.Path(exists=True), help="Load from specific file")
@click.option("--autosave", "-a", "from_autosave", is_flag=True, help="Load from autosave")
def load(slot: Optional[int], file: Optional[str], from_autosave: bool) -> None:
    """Load a saved game.

    SLOT is the save slot number (1-99).
    """
    try:
        if file:
            saved = load_game(1)  # Placeholder - would need load_game_from_path
            console.print(f"[green]Loaded game from {file}[/green]")
        elif from_autosave:
            saved = load_autosave()
            console.print("[green]Loaded from autosave[/green]")
        elif slot:
            saved = load_game(slot)
            console.print(f"[green]Loaded game from slot {slot}[/green]")
        else:
            # Show available saves
            _show_saves()
            return

        game_state = saved.game_state
        company = game_state.get_company(1)
        console.print(f"  Company: {company.name}")
        console.print(f"  Week: {game_state.current_week}")
        console.print()

        _play_game(game_state, slot if slot else 0)

    except LoadError as e:
        console.print(f"[red]Error loading game: {e}[/red]")
        sys.exit(1)


@cli.command()
def saves() -> None:
    """List all saved games."""
    _show_saves()


@cli.command()
@click.option("--decs", "-d", type=click.Path(exists=True), required=True, help="DECS decision file")
@click.option("--state", "-s", type=click.Path(exists=True), help="Game state file to load")
@click.option("--slot", type=int, help="Load game from this save slot")
@click.option("--output", "-o", type=click.Path(), help="Output REPT file path")
@click.option("--autosave/--no-autosave", default=True, help="Auto-save after processing")
def process(
    decs: str,
    state: Optional[str],
    slot: Optional[int],
    output: Optional[str],
    autosave_enabled: bool,
) -> None:
    """Process a week using a DECS decision file.

    This is useful for batch processing or integration with external tools.
    """
    # Load game state
    if slot:
        try:
            saved = load_game(slot)
            game_state = saved.game_state
            config = saved.config
        except LoadError as e:
            console.print(f"[red]Error loading game: {e}[/red]")
            sys.exit(1)
    else:
        # Create new game state
        game_state = GameState.create_single_player(
            game_id=str(uuid.uuid4())[:8],
            company_name="Batch Company",
        )
        config = None

    # Parse decisions
    try:
        decisions = parse_decs(decs)
    except Exception as e:
        console.print(f"[red]Error parsing DECS file: {e}[/red]")
        sys.exit(1)

    # Process week
    company = game_state.get_company(1)
    simulation = Simulation(config=config or get_default_config())

    try:
        result = simulation.process_week(company, decisions)
    except ValueError as e:
        console.print(f"[red]Simulation error: {e}[/red]")
        sys.exit(1)

    # Update game state
    game_state = game_state.update_company(result.updated_company)
    game_state = game_state.model_copy(
        update={"current_week": result.updated_company.current_week}
    )

    # Output report
    if output:
        with open(output, "w") as f:
            f.write(write_rept_human_readable(result.weekly_report))
        console.print(f"[green]Report written to {output}[/green]")
    else:
        _display_report(result.weekly_report)

    # Auto-save
    if autosave_enabled and slot:
        try:
            save_game(game_state, slot, config=config)
            console.print(f"[green]Game saved to slot {slot}[/green]")
        except SaveError as e:
            console.print(f"[yellow]Warning: Failed to save: {e}[/yellow]")


@cli.command()
def info() -> None:
    """Show information about PROSIM."""
    console.print(Panel.fit(
        """[bold blue]PROSIM - Production Management Simulation[/bold blue]

[bold]Original Authors (1968-1996):[/bold]
  - Paul S. Greenlaw
  - Michael P. Hottenstein
  - Chao-Hsien Chu

[bold]Reconstruction (2024):[/bold]
  - Nelson DeWitt

This is a clean-room reconstruction of the original PROSIM simulation
game, rebuilt for educational preservation and modern use.

[dim]For more information, see:
  - README.md
  - IMPLEMENTATION_PLAN.md
  - archive/docs/PROSIM_CASE_STUDY.md[/dim]""",
        title="About PROSIM",
        border_style="blue",
    ))


# =============================================================================
# Interactive Game Play
# =============================================================================


def _play_game(game_state: GameState, save_slot: Optional[int] = None) -> None:
    """Main interactive game loop."""
    config = get_default_config()
    simulation = Simulation(config=config, random_seed=game_state.random_seed)

    while game_state.is_active:
        company = game_state.get_company(1)

        # Show current state
        _display_game_state(company)

        # Get player choice
        console.print("\n[bold]What would you like to do?[/bold]")
        console.print("  [1] Enter decisions and process week")
        console.print("  [2] View last report")
        console.print("  [3] Save game")
        console.print("  [4] Help")
        console.print("  [q] Quit")
        console.print()

        choice = Prompt.ask("Choice", choices=["1", "2", "3", "4", "q"], default="1")

        if choice == "1":
            # Enter decisions
            decisions = _get_decisions_interactive(company)
            if decisions is None:
                continue

            # Process week
            try:
                result = simulation.process_week(company, decisions)
                game_state = game_state.update_company(result.updated_company)
                game_state = game_state.model_copy(
                    update={"current_week": result.updated_company.current_week}
                )

                # Display report
                _display_report(result.weekly_report)

                # Auto-save
                try:
                    autosave(game_state, config=config)
                except SaveError:
                    pass

            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")

        elif choice == "2":
            if company.latest_report:
                _display_report(company.latest_report)
            else:
                console.print("[yellow]No reports yet.[/yellow]")

        elif choice == "3":
            _save_game_interactive(game_state, save_slot)

        elif choice == "4":
            _show_help()

        elif choice == "q":
            if Confirm.ask("Save before quitting?", default=True):
                _save_game_interactive(game_state, save_slot)
            break

    if game_state.is_complete:
        console.print(Panel.fit(
            "[bold green]Game Complete![/bold green]\n\n"
            f"You reached week {game_state.max_weeks}.",
            border_style="green",
        ))


def _get_decisions_interactive(company: Company) -> Optional[Decisions]:
    """Get weekly decisions from user input."""
    console.print()
    console.print(Panel.fit(
        f"[bold]Week {company.current_week} Decisions[/bold]",
        border_style="cyan",
    ))

    try:
        # Budgets
        quality_budget = FloatPrompt.ask(
            "Quality Planning Budget ($)",
            default=0.0,
        )
        maintenance_budget = FloatPrompt.ask(
            "Plant Maintenance Budget ($)",
            default=0.0,
        )

        # Raw materials orders
        console.print("\n[bold]Raw Materials Orders:[/bold]")
        rm_regular = FloatPrompt.ask(
            "  Regular order (3-week lead)",
            default=0.0,
        )
        rm_expedited = FloatPrompt.ask(
            "  Expedited order (1-week lead, +$1200)",
            default=0.0,
        )

        # Parts orders
        console.print("\n[bold]Purchased Parts Orders (1-week lead):[/bold]")
        parts_x = FloatPrompt.ask("  X' parts", default=0.0)
        parts_y = FloatPrompt.ask("  Y' parts", default=0.0)
        parts_z = FloatPrompt.ask("  Z' parts", default=0.0)

        # Machine assignments
        console.print("\n[bold]Machine Assignments:[/bold]")
        console.print("[dim]Parts Dept (1-4): produce X'=1, Y'=2, Z'=3[/dim]")
        console.print("[dim]Assembly Dept (5-9): produce X=1, Y=2, Z=3[/dim]")
        console.print("[dim]Enter 0 hours to not schedule. Enter 't' to train operator.[/dim]")
        console.print()

        machine_decisions = []
        for machine_id in range(1, 10):
            dept = "Parts" if machine_id <= 4 else "Assembly"
            op = company.workforce.get_operator(machine_id)
            trained_str = "[green]Trained[/green]" if op and op.is_trained else "[yellow]Untrained[/yellow]"

            console.print(f"  Machine {machine_id} ({dept}) - Operator {trained_str}")

            hours_input = Prompt.ask(
                f"    Hours (0-50 or 't' for training)",
                default="40",
            )

            if hours_input.lower() == "t":
                # Send for training
                part_type = 1
                hours = 0.0
                training = True
            else:
                try:
                    hours = float(hours_input)
                    hours = max(0, min(50, hours))
                except ValueError:
                    hours = 0.0
                training = False

                if hours > 0:
                    part_type = IntPrompt.ask(
                        f"    Part type (1=X, 2=Y, 3=Z)",
                        default=1,
                    )
                    part_type = max(1, min(3, part_type))
                else:
                    part_type = 1

            machine_decisions.append(MachineDecision(
                machine_id=machine_id,
                send_for_training=training,
                part_type=part_type,
                scheduled_hours=hours,
            ))

        # Build decisions
        decisions = Decisions(
            week=company.current_week,
            company_id=company.company_id,
            quality_budget=quality_budget,
            maintenance_budget=maintenance_budget,
            raw_materials_regular=rm_regular,
            raw_materials_expedited=rm_expedited,
            part_orders=PartOrders(
                x_prime=parts_x,
                y_prime=parts_y,
                z_prime=parts_z,
            ),
            machine_decisions=machine_decisions,
        )

        # Validate decisions
        validation_result = validate_decisions(decisions, company)

        # Show any warnings
        if validation_result.warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in validation_result.warnings:
                console.print(f"  [yellow]- {warning.message}[/yellow]")
                if warning.suggestion:
                    console.print(f"    [dim]{warning.suggestion}[/dim]")

        # Show errors and abort if invalid
        if not validation_result.valid:
            console.print("\n[red]Validation errors:[/red]")
            for error in validation_result.errors:
                console.print(f"  [red]- {error.field}: {error.message}[/red]")
                if error.suggestion:
                    console.print(f"    [dim]{error.suggestion}[/dim]")
            console.print("\n[red]Please correct errors and try again.[/red]")
            return None

        # Confirm
        console.print()
        if not Confirm.ask("Submit these decisions?", default=True):
            return None

        return decisions

    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Decisions cancelled.[/yellow]")
        return None


def _save_game_interactive(game_state: GameState, default_slot: Optional[int]) -> None:
    """Interactive save game dialog."""
    saves = list_saves()

    if saves:
        console.print("\n[bold]Existing saves:[/bold]")
        for save in saves[:5]:
            slot_str = f"Slot {save.save_slot}" if save.save_slot > 0 else "Autosave"
            console.print(f"  [{save.save_slot}] {slot_str}: {save.save_name}")

    slot = IntPrompt.ask(
        "Save to slot",
        default=default_slot or 1,
    )

    name = Prompt.ask(
        "Save name",
        default=f"Week {game_state.current_week}",
    )

    try:
        save_game(game_state, slot, save_name=name)
        console.print(f"[green]Game saved to slot {slot}[/green]")
    except SaveError as e:
        console.print(f"[red]Failed to save: {e}[/red]")


# =============================================================================
# Display Functions
# =============================================================================


def _display_game_state(company: Company) -> None:
    """Display current game state summary."""
    console.print()
    console.print(Panel.fit(
        f"[bold]{company.name}[/bold]\n"
        f"Week {company.current_week} | Total Costs: ${company.total_costs:,.2f}",
        title="Current State",
        border_style="blue",
    ))

    # Inventory summary
    inv = company.inventory
    table = Table(title="Inventory Summary", box=None)
    table.add_column("Item")
    table.add_column("Quantity", justify="right")

    table.add_row("Raw Materials", f"{inv.raw_materials.ending:,.0f}")
    table.add_row("Parts X'", f"{inv.parts.x_prime.ending:,.0f}")
    table.add_row("Parts Y'", f"{inv.parts.y_prime.ending:,.0f}")
    table.add_row("Parts Z'", f"{inv.parts.z_prime.ending:,.0f}")
    table.add_row("Products X", f"{inv.products.x.ending:,.0f}")
    table.add_row("Products Y", f"{inv.products.y.ending:,.0f}")
    table.add_row("Products Z", f"{inv.products.z.ending:,.0f}")

    console.print(table)


def _display_report(report: WeeklyReport) -> None:
    """Display a weekly report."""
    console.print()
    console.print(Panel.fit(
        f"[bold]Week {report.week} Report[/bold]",
        border_style="green",
    ))

    # Costs summary
    costs = report.weekly_costs
    table = Table(title="Costs This Week", box=None)
    table.add_column("Category")
    table.add_column("X", justify="right")
    table.add_column("Y", justify="right")
    table.add_column("Z", justify="right")
    table.add_column("Total", justify="right")

    # Per-product costs
    x = costs.x_costs
    y = costs.y_costs
    z = costs.z_costs

    def format_cost(val: float) -> str:
        return f"${val:,.0f}" if val > 0 else "-"

    table.add_row("Labor", format_cost(x.labor), format_cost(y.labor), format_cost(z.labor),
                  format_cost(x.labor + y.labor + z.labor))
    table.add_row("Equipment", format_cost(x.equipment_usage), format_cost(y.equipment_usage),
                  format_cost(z.equipment_usage),
                  format_cost(x.equipment_usage + y.equipment_usage + z.equipment_usage))
    table.add_row("Raw Materials", format_cost(x.raw_materials), format_cost(y.raw_materials),
                  format_cost(z.raw_materials),
                  format_cost(x.raw_materials + y.raw_materials + z.raw_materials))

    x_total = x.total
    y_total = y.total
    z_total = z.total
    table.add_row("[bold]Sub-Total[/bold]", f"[bold]${x_total:,.0f}[/bold]",
                  f"[bold]${y_total:,.0f}[/bold]", f"[bold]${z_total:,.0f}[/bold]",
                  f"[bold]${x_total + y_total + z_total:,.0f}[/bold]")

    console.print(table)

    # Overhead
    oh = costs.overhead
    overhead_total = oh.total
    console.print(f"\n[bold]Overhead:[/bold] ${overhead_total:,.0f}")
    console.print(f"  Quality: ${oh.quality_planning:,.0f} | Maintenance: ${oh.plant_maintenance:,.0f}")
    console.print(f"  Training: ${oh.training_cost:,.0f} | Fixed: ${oh.fixed_expense:,.0f}")

    # Grand total
    grand_total = x_total + y_total + z_total + overhead_total
    console.print(f"\n[bold green]Total Week Costs: ${grand_total:,.0f}[/bold green]")

    # Production summary
    console.print()
    prod = report.production
    table = Table(title="Production", box=None)
    table.add_column("Machine")
    table.add_column("Part")
    table.add_column("Hours", justify="right")
    table.add_column("Production", justify="right")
    table.add_column("Rejects", justify="right")

    for mp in prod.parts_department:
        table.add_row(
            f"M{mp.machine_id}",
            mp.part_type,
            f"{mp.productive_hours:.1f}",
            f"{mp.production:.0f}",
            f"{mp.rejects:.0f}",
        )
    table.add_row("---", "---", "---", "---", "---")
    for mp in prod.assembly_department:
        table.add_row(
            f"M{mp.machine_id}",
            mp.part_type,
            f"{mp.productive_hours:.1f}",
            f"{mp.production:.0f}",
            f"{mp.rejects:.0f}",
        )

    console.print(table)

    # Inventory
    console.print()
    inv = report.inventory
    table = Table(title="Inventory", box=None)
    table.add_column("Item")
    table.add_column("Beginning", justify="right")
    table.add_column("Received", justify="right")
    table.add_column("Produced", justify="right")
    table.add_column("Used", justify="right")
    table.add_column("Ending", justify="right")

    table.add_row(
        "Raw Materials",
        f"{inv.raw_materials.beginning_inventory:,.0f}",
        f"{inv.raw_materials.orders_received:,.0f}",
        "-",
        f"{inv.raw_materials.used_in_production:,.0f}",
        f"{inv.raw_materials.ending_inventory:,.0f}",
    )

    for part_name, part in [("X'", inv.parts_x), ("Y'", inv.parts_y), ("Z'", inv.parts_z)]:
        table.add_row(
            f"Parts {part_name}",
            f"{part.beginning_inventory:,.0f}",
            f"{part.orders_received:,.0f}",
            f"{part.production_this_week:,.0f}",
            f"{part.used_in_production:,.0f}",
            f"{part.ending_inventory:,.0f}",
        )

    for prod_name, product in [("X", inv.products_x), ("Y", inv.products_y), ("Z", inv.products_z)]:
        table.add_row(
            f"Product {prod_name}",
            f"{product.beginning_inventory:,.0f}",
            "-",
            f"{product.production_this_week:,.0f}",
            f"{product.demand_this_week:,.0f}",
            f"{product.ending_inventory:,.0f}",
        )

    console.print(table)

    # Press enter to continue
    console.print()
    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")


def _show_saves() -> None:
    """Display list of saved games."""
    saves = list_saves()

    if not saves:
        console.print("[yellow]No saved games found.[/yellow]")
        return

    table = Table(title="Saved Games", box=None)
    table.add_column("Slot", justify="right")
    table.add_column("Name")
    table.add_column("Week", justify="right")
    table.add_column("Costs", justify="right")
    table.add_column("Updated")

    for save in saves:
        slot_str = str(save.save_slot) if save.save_slot > 0 else "Auto"
        table.add_row(
            slot_str,
            save.save_name,
            str(save.current_week),
            f"${save.total_costs:,.0f}",
            save.updated_at[:16].replace("T", " "),
        )

    console.print(table)


def _show_help() -> None:
    """Display help information."""
    console.print(Panel.fit(
        """[bold]PROSIM Help[/bold]

[bold cyan]Objective:[/bold cyan]
Manage a manufacturing company producing three products (X, Y, Z).
Minimize costs while meeting demand.

[bold cyan]Production Flow:[/bold cyan]
Raw Materials -> Parts Dept (X', Y', Z') -> Assembly Dept (X, Y, Z)

[bold cyan]Machines:[/bold cyan]
- Parts Department: Machines 1-4
  - X': 60 parts/hour
  - Y': 50 parts/hour
  - Z': 40 parts/hour
- Assembly Department: Machines 5-9
  - X: 40 units/hour
  - Y: 30 units/hour
  - Z: 20 units/hour

[bold cyan]Lead Times:[/bold cyan]
- Raw Materials (Regular): 3 weeks
- Raw Materials (Expedited): 1 week (+$1,200)
- Purchased Parts: 1 week

[bold cyan]Operators:[/bold cyan]
- Untrained operators: ~60-90% efficiency
- Trained operators: ~95-100% efficiency
- Training takes 1 week (operator unavailable)

[bold cyan]Shipping:[/bold cyan]
Products ship every 4 weeks. Unfulfilled demand carries over with penalty.""",
        border_style="cyan",
    ))


# =============================================================================
# Entry Point
# =============================================================================


if __name__ == "__main__":
    cli()
