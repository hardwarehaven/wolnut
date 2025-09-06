# Contributing to WOLNUT

First off, thank you for considering contributing to WOLNUT! It's people like you that make open source great.

Following these guidelines helps to communicate that you respect the time of the developers managing and developing this project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

WOLNUT is an open source project and we love to receive contributions from our community — you! There are many ways to contribute, from writing tutorials or blog posts, improving the documentation, submitting bug reports and feature requests, or writing code which can be incorporated into WOLNUT itself.

## Code of Conduct

We have a Code of Conduct that we expect all contributors to adhere to. Please take a moment to read it before you get started.

## How Can I Contribute?

There are many ways to contribute to the project.

### Reporting Bugs

If you find a bug, please make sure it hasn't already been reported by searching on GitHub under Issues.

If you're unable to find an open issue addressing the problem, open a new one. Be sure to include a **title and clear description**, as much relevant information as possible, and a **code sample or an executable test case** demonstrating the expected behavior that is not occurring.

### Suggesting Enhancements

If you have an idea for an enhancement, please open an issue to discuss it. This allows us to coordinate our efforts and prevent duplication of work.

### Your First Code Contribution

Unsure where to begin contributing to WOLNUT? You can start by looking through these `good-first-issue` and `help-wanted` issues:

*   **Good First Issues** - issues which should only require a few lines of code, and a test or two.
*   **Help Wanted Issues** - issues which should be a bit more involved than `good-first-issue` issues.

## Development Setup

Ready to contribute code? Here’s how to set up WOLNUT for local development.

1.  **Fork the repository** on GitHub.

2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/your-username/wolnut.git
    cd wolnut
    ```

3.  **Set up your environment.** This project uses uv to manage dependencies and virtual environments.
    The easiest way to do this is to run the setup_env.sh script:
    ```bash
    script/setup_env.sh
    ```
    Its safe to run this multiple times and will automatically update dependencies as needed.

    #### Otherwise, you can do the steps manually:
        First, create a virtual environment:
        ```bash
        uv venv
        ```

        Then, activate it:
        ```bash
        source .venv/bin/activate
        ```

        Install dependencies, including development tools:
        ```bash
        uv sync --dev
        ```

4.  **Create a `config.yaml`** file from the example to run the application locally.
    ```bash
    cp config.example.yaml config.yaml
    ```
    Be sure to edit `config.yaml` with your local NUT server details.

5. **Optionally, run the unit tests to verify things are working correctly for your setup.
    ```bash
    script/tests
    ```
    All tests should show `PASSED`

## Making Changes

1.  Create a new branch for your changes:
    ```bash
    git checkout -b your-feature-name
    ```

2.  Make your changes in the source code.

3.  **Format your code.** We use `black` for code formatting.
    ```bash
    script/linting
    ```

4.  **Run the tests.** Add or update tests as appropriate in the `tests/` directory.
    ```bash
    script/tests
    ```

5.  **Optionally: View your current code coverage**
    ```bash
    script/coverage
    ```
    A detailed coverage report can be viewed by browsing the coverage/ directory.

6.  **Optionally: Clean the repo**
    ```bash
    script/clean
    ```
    Will remove temporary files and build values

7.  **Commit your changes** with a clear commit message.

8.  **Push your branch** to your fork on GitHub.

9.  **Open a pull request** to the `main` branch of the original repository.  
    This will automatically trigger a linting check and unit tests for our supported platforms and python versions.

## Pull Request Guidelines

Before you submit a pull request, please check that it meets these guidelines:

1.  The pull request should include tests for any new or changed functionality.
2.  If the pull request adds functionality, the `README.md` or other documentation should be updated.
3.  The test suite must pass.
4.  The code must be formatted with `black`.

---

Thank you for your contribution!
