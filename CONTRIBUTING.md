# Contributing to Capture Project

We welcome contributions from the community! Here's how you can help:

## How to Contribute

1. **Fork** the repository
2. Create a new branch for your feature or bugfix:
   ```
   git checkout -b feature/your-feature-name
   ```
3. Make your changes
4. Ensure your code follows the project's style guide
5. Write tests if applicable
6. Commit your changes with a descriptive commit message
7. Push to your fork and submit a pull request

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/capture_mac.git
   cd capture_mac
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep lines under 88 characters (Black's default line length)

## Testing

Run tests with:
```bash
pytest
```

## Pull Request Guidelines

- Keep pull requests focused on a single feature or bugfix
- Update the README.md if your changes affect the user interface
- Ensure all tests pass before submitting
- Add tests for new features or bug fixes

## Reporting Issues

When reporting issues, please include:
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Any relevant error messages or logs

## Code of Conduct

This project adheres to the Contributor Covenant [code of conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.
