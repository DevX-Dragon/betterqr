# Contributing to BetterQR

We welcome contributions to BetterQR! Whether it's bug reports, feature requests, or code contributions, your help is greatly appreciated. Please take a moment to review this document to make the contribution process as smooth as possible.

## Table of Contents

1.  [Code of Conduct](#code-of-conduct)
2.  [How to Report Bugs](#how-to-report-bugs)
3.  [How to Suggest Enhancements](#how-to-suggest-enhancements)
4.  [Your First Code Contribution](#your-first-code-contribution)
5.  [Pull Request Guidelines](#pull-request-guidelines)
6.  [Development Setup](#development-setup)

## Code of Conduct

This project and everyone participating in it is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [maintainer's email or issue tracker].

## How to Report Bugs

If you find a bug, please open an issue on the [GitHub Issue Tracker](https://github.com/DevX-Dragon/BetterQR/issues) and include as much detail as possible. A good bug report typically includes:

*   **Steps to reproduce**: Clear and concise instructions on how to replicate the bug.
*   **Expected behavior**: What you expected to happen.
*   **Actual behavior**: What actually happened.
*   **Screenshots/GIFs**: If applicable, visual aids can be very helpful.
*   **Environment**: Your operating system, Python version, BetterQR version, and any other relevant dependencies.
*   **Example code**: A minimal, reproducible example that demonstrates the bug.

## How to Suggest Enhancements

We love new ideas! If you have a suggestion for an enhancement or a new feature, please open an issue on the [GitHub Issue Tracker](https://github.com/DevX-Dragon/BetterQR/issues). Please describe the enhancement in detail, including:

*   **Problem**: What problem does this enhancement solve?
*   **Proposed solution**: How do you envision this enhancement working?
*   **Use cases**: Examples of how this feature would be used.
*   **Alternatives**: Have you considered any alternative solutions or features?

## Your First Code Contribution

If you're looking to make your first code contribution, look for issues labeled `good first issue` on the [GitHub Issue Tracker](https://github.com/DevX-Dragon/BetterQR/issues). These issues are specifically designed to be approachable for new contributors.

## Pull Request Guidelines

Before submitting a pull request, please ensure the following:

1.  **Fork the repository** and create your branch from `main`.
2.  **Install dependencies**: Run `pip install -e .` in your development environment.
3.  **Code style**: Adhere to the existing code style. We use `black` and `isort` for formatting.
4.  **Tests**: Add unit tests for new features or bug fixes. Ensure all existing tests pass.
5.  **Documentation**: Update relevant documentation (e.g., `README.md`, `DOCUMENTATION.md`) for any changes.
6.  **Commit messages**: Write clear and concise commit messages.
7.  **One feature/bug per PR**: Keep your pull requests focused on a single change.

## Development Setup

To set up your development environment:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/DevX-Dragon/BetterQR.git
    cd BetterQR
    ```
2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  **Install in editable mode**:
    ```bash
    pip install -e .
    ```
4.  **Install development dependencies** (if any, e.g., for testing or linting):
    ```bash
    # Example: pip install pytest black isort
    ```

Now you can make changes to the code and test them locally.
