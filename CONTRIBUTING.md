# Contributing to PROSIM Reconstruction

Thank you for your interest in contributing to the PROSIM Reconstruction Project! This document provides guidelines for contributing.

## Table of Contents

1. [Ways to Contribute](#ways-to-contribute)
2. [Development Setup](#development-setup)
3. [Code Guidelines](#code-guidelines)
4. [Adding Translations](#adding-translations)
5. [Reporting Issues](#reporting-issues)
6. [Submitting Changes](#submitting-changes)
7. [Historical Data Contributions](#historical-data-contributions)

---

## Ways to Contribute

### Code Contributions
- Bug fixes
- New features
- Performance improvements
- Documentation improvements

### Non-Code Contributions
- **DECS/REPT Files**: Historical simulation data for validation
- **Translations**: Help make PROSIM accessible in more languages
- **Documentation**: Improve guides, fix typos, add examples
- **Testing**: Report bugs, test on different platforms
- **Historical Information**: Documentation about the original PROSIM

---

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/prosim-reconstruction.git
cd prosim-reconstruction

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev]"

# Run tests to verify setup
pytest
```

### Development Tools

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=prosim --cov-report=term-missing

# Type checking
mypy prosim

# Linting
ruff check prosim tests

# Formatting
black prosim tests
```

---

## Code Guidelines

### Python Style

- **Python Version**: 3.11+
- **Type Hints**: Required for all public functions
- **Docstrings**: Required for all public modules, classes, and functions
- **Formatting**: Black with default settings
- **Linting**: Ruff with project configuration
- **Testing**: Pytest with 80%+ coverage target

### Example Function

```python
def calculate_production(
    scheduled_hours: float,
    efficiency: float,
    production_rate: float,
) -> float:
    """Calculate net production for a machine.

    Args:
        scheduled_hours: Hours scheduled for production
        efficiency: Operator efficiency (0.0-1.0)
        production_rate: Units per hour at 100% efficiency

    Returns:
        Net units produced after efficiency applied

    Raises:
        ValueError: If efficiency is not between 0 and 1
    """
    if not 0.0 <= efficiency <= 1.0:
        raise ValueError(f"Efficiency must be between 0 and 1, got {efficiency}")

    productive_hours = scheduled_hours * efficiency
    return productive_hours * production_rate
```

### Commit Messages

Follow conventional commits format:

```
type: short description

Longer description if needed.

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code restructuring

---

## Adding Translations

PROSIM uses JSON files for internationalization. To add a new language:

### 1. Create the Locale File

Copy the English locale as a template:

```bash
cp prosim/i18n/locales/en.json prosim/i18n/locales/XX.json
```

Replace `XX` with the [ISO 639-1 language code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) (e.g., `fr`, `de`, `ja`).

### 2. Translate the Strings

Edit the new file and translate all values:

```json
{
  "app": {
    "name": "PROSIM",
    "tagline": "Production Management Simulation"  // Translate this
  },
  "menu": {
    "new_game": "New Game",      // Translate this
    "load_game": "Load Game",    // Translate this
    ...
  }
}
```

**Important:**
- Keep JSON keys unchanged
- Translate only the string values
- Preserve any placeholders like `{week}` or `{version}`
- Test your translation by running the CLI with `--lang XX`

### 3. Test the Translation

```bash
# Run CLI in your language
prosim --lang XX new --name "Test"

# Verify all strings appear correctly
```

### 4. Submit a Pull Request

Include in your PR:
- The new locale file
- Any updates to documentation
- Note your language/translation background if relevant

### Currently Available Languages

| Code | Language | Status |
|------|----------|--------|
| `en` | English | Complete |
| `es` | Spanish | Complete |

---

## Reporting Issues

### Bug Reports

When reporting a bug, please include:

1. **Description**: What happened vs. what you expected
2. **Steps to Reproduce**: Minimal steps to trigger the bug
3. **Environment**: OS, Python version, PROSIM version
4. **Error Messages**: Full error text and stack traces
5. **Screenshots**: If applicable

**Template:**
```markdown
## Description
[What went wrong]

## Steps to Reproduce
1. Run `prosim new --name "Test"`
2. Enter decision values...
3. See error

## Expected Behavior
[What should have happened]

## Environment
- OS: macOS 14.0 / Windows 11 / Ubuntu 22.04
- Python: 3.11.5
- PROSIM: 1.0.0

## Error Output
```
[Paste error message here]
```
```

### Feature Requests

For feature requests, please describe:

1. **Use Case**: What problem does this solve?
2. **Proposed Solution**: How would it work?
3. **Alternatives**: Other approaches considered?
4. **Impact**: Who benefits from this feature?

---

## Submitting Changes

### Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch from `main`
3. **Make** your changes with tests
4. **Run** the test suite (`pytest`)
5. **Run** linting and type checks (`ruff check`, `mypy prosim`)
6. **Commit** with conventional commit messages
7. **Push** to your fork
8. **Open** a Pull Request

### Pull Request Template

```markdown
## Description
[What does this PR do?]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactoring
- [ ] Other (describe)

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style
- [ ] Self-review performed
- [ ] Documentation updated
- [ ] No breaking changes (or documented if breaking)
```

### Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, your PR will be merged

---

## Historical Data Contributions

### DECS/REPT Files

If you have original PROSIM decision or report files:

1. **Open an Issue** describing what you have
2. **Share the files** (attach to issue or email to maintainers)
3. We'll validate them against our simulation
4. Your contribution will be acknowledged

**What we're looking for:**
- DECS*.DAT files (decision inputs)
- REPT*.DAT files (simulation reports)
- Any sequence of files from continuous gameplay
- Files from different courses/universities

### Other Historical Materials

We're also interested in:
- Original textbook: "PROSIM: A Production Management Simulation"
- Instructor guides or manuals
- Course syllabi mentioning PROSIM
- Screenshots or printouts
- Academic papers referencing PROSIM
- Personal recollections of how the game worked

### Privacy

If your files contain personal information (names, email addresses), let us know and we can anonymize them before including in the project.

---

## Questions?

- **For questions about contributing**: Open a GitHub Discussion
- **For bugs or feature requests**: Open a GitHub Issue
- **For historical materials**: Open an Issue or contact maintainers directly

---

## Code of Conduct

### Our Pledge

We are committed to making participation in this project a welcoming experience for everyone, regardless of background or experience level.

### Our Standards

- Be respectful and inclusive
- Focus on constructive feedback
- Accept different viewpoints gracefully
- Prioritize what's best for the community

### Enforcement

Unacceptable behavior may result in temporary or permanent bans from the project.

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

*Thank you for contributing to the preservation of educational software history!*
