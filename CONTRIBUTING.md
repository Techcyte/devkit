# Contributing to Techcyte Devkit

Thank you for your interest in contributing to the `Techcyte Devkit` repository. We welcome contributions that improve our example code, documentation, or overall user experience. This guide outlines how to contribute effectively.

## How to Contribute

### 1. Reporting Issues
If you find bugs, have feature requests, or notice documentation errors:
- Check the [issue tracker](https://github.com/Techcyte/devkit/issues) to ensure the issue hasn’t been reported.
- Open a new issue with a clear title and description, including steps to reproduce (if applicable).
- Use the provided issue templates, if available.

### 2. Submitting Pull Requests
We encourage contributions such as bug fixes, new examples, or documentation improvements. Follow these steps:
1. **Fork the Repository**: Create a fork of `Techcyte Devkit` on GitHub.
2. **Clone Your Fork**:
   ```bash
   git clone https://github.com/Techcyte/devkit.git
   ```
3. **Create a Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make Changes**:
   - Ensure code follows the style guidelines in the repository (e.g., consistent formatting).
   - Update or add documentation in the relevant `docs/` (e.g., `model-hosting-service` or `api-bridge`).
   - Test your changes locally to ensure they work with Techcyte’s system. Run `mkdocs serve` to test locally. Visit http://127.0.0.1:8000 to view locally.
5. **Commit Changes**:
   - Use clear, descriptive commit messages.
   - Example: `Add example for API bridge authentication flow`.
6. **Push to Your Fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Open a Pull Request**:
   - Submit a pull request to the `main` branch of `techcyte/devkit`.
   - Include a clear description of your changes and reference any related issues.
   - Use the provided pull request template, if available.

### 3. Code and Documentation Guidelines
- **Code**:
  - Follow existing code patterns in the repository.
  - Ensure examples are clear, functional, and well-commented.
  - Test code against Techcyte’s model hosting service or API bridge.
- **Documentation**:
  - Use clear, concise language.
  - Follow Markdown formatting conventions.
  - Update relevant READMEs in `docs/` as needed.
- **Licensing**: By contributing, you agree that your contributions will be licensed under the [MIT License](./LICENSE).

## Getting Help
If you have questions or need assistance:
- Check the [README.md](./README.md) for general guidance.
- Reach out via the [issue tracker](https://github.com/Techcyte/devkit/issues).
- Contact our support team at [info@techcyte.com](mailto:info@techcyte.com).

## Acknowledgements
We appreciate all contributions, big or small. Contributors may be acknowledged in release notes or the repository’s documentation.
