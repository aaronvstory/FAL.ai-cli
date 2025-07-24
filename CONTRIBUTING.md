# 🤝 Contributing to FAL.AI Video Generator CLI

Thank you for your interest in contributing to the FAL.AI Video Generator CLI! This document provides guidelines and information for contributors.

## 🌟 Ways to Contribute

- 🐛 **Bug Reports**: Help us identify and fix issues
- 💡 **Feature Requests**: Suggest new features and improvements
- 🔧 **Code Contributions**: Submit bug fixes and new features
- 📚 **Documentation**: Improve or translate documentation
- 🧪 **Testing**: Help test new features and report issues
- 🎨 **UI/UX**: Contribute to interface design and user experience

## 🚀 Quick Start for Contributors

### Prerequisites
- Python 3.8 or higher
- Git for version control
- FAL.AI API key for testing (get from [fal.ai/dashboard](https://fal.ai/dashboard))

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/FAL.ai-cli.git
   cd FAL.ai-cli
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

4. **Set up Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your FAL_KEY
   ```

5. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

## 🔧 Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/amazing-new-feature
# or
git checkout -b bugfix/fix-critical-issue
```

### 2. Make Your Changes
- Follow the existing code style and patterns
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Commit Your Changes
```bash
git add .
git commit -m "feat: add amazing new feature

- Detailed description of changes
- Any breaking changes noted
- Closes #issue-number"
```

### 4. Push and Create Pull Request
```bash
git push origin feature/amazing-new-feature
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference to related issues
- Screenshots for UI changes
- Test results

## 📝 Code Style Guidelines

### Python Code Style
We follow [PEP 8](https://pep8.org/) with some customizations:

```bash
# Format code with Black
black .

# Lint with flake8
flake8 .

# Type checking with mypy
mypy . --ignore-missing-imports
```

### Key Style Points
- **Line Length**: Maximum 88 characters (Black default)
- **Imports**: Use absolute imports, group by standard/third-party/local
- **Docstrings**: Use Google-style docstrings
- **Type Hints**: Add type hints for all function parameters and returns
- **Comments**: Write clear, concise comments explaining "why" not "what"

### Example Code Structure
```python
#!/usr/bin/env python3
"""
Module docstring describing the purpose.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from third_party_lib import SomeClass

from .local_module import LocalClass


class ExampleClass:
    """Class docstring with clear description.
    
    Args:
        param1: Description of parameter
        param2: Description of parameter
        
    Attributes:
        attr1: Description of attribute
    """
    
    def __init__(self, param1: str, param2: Optional[int] = None):
        self.attr1 = param1
        self.attr2 = param2 or 0
    
    def example_method(self, data: Dict[str, str]) -> List[str]:
        """Method docstring with description.
        
        Args:
            data: Dictionary containing input data
            
        Returns:
            List of processed strings
            
        Raises:
            ValueError: When data is invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        # Process data and return results
        return list(data.keys())
```

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── test_main.py              # Core application tests
├── test_launcher_system.py   # Launcher system tests
├── test_security.py          # Security feature tests
├── test_performance.py       # Performance tests
└── conftest.py              # Shared test fixtures
```

### Writing Tests
```python
import pytest
from unittest.mock import Mock, patch

from main import VideoGenerator


class TestVideoGenerator:
    """Test suite for VideoGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create VideoGenerator instance for testing."""
        return VideoGenerator(api_key="test-key")
    
    def test_initialization(self, generator):
        """Test VideoGenerator initializes correctly."""
        assert generator.api_key == "test-key"
        assert generator.models is not None
    
    @patch('main.fal_client')
    def test_generate_video(self, mock_client, generator):
        """Test video generation with mocked client."""
        mock_client.subscribe.return_value = {"video_url": "test.mp4"}
        
        result = generator.generate_video("test.jpg", "test prompt")
        
        assert result["video_url"] == "test.mp4"
        mock_client.subscribe.assert_called_once()
```

### Test Coverage Requirements
- **Minimum Coverage**: 80% overall
- **Critical Paths**: 95% coverage for security and core functionality
- **New Features**: Must include comprehensive tests
- **Bug Fixes**: Must include regression tests

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=main --cov=security --cov=performance --cov-report=html

# Run specific test file
pytest tests/test_main.py -v

# Run tests matching pattern
pytest tests/ -k "test_launcher" -v
```

## 🏗️ Architecture Guidelines

### Project Structure
```
FAL.ai-cli/
├── FAL_LAUNCHER.py           # Main entry point
├── main.py                   # CLI application
├── web_app.py               # Web interface
├── security.py              # Security utilities
├── performance.py           # Performance features
├── core/                    # Core modules
│   ├── launcher/           # Launcher system
│   └── gui/               # GUI components
├── web/                    # Web assets
├── tests/                  # Test suite
├── config/                 # Configuration
└── data/                   # Data storage
```

### Module Design Principles
1. **Single Responsibility**: Each module has one clear purpose
2. **Loose Coupling**: Minimize dependencies between modules
3. **High Cohesion**: Related functionality grouped together
4. **Dependency Injection**: Use dependency injection for testability
5. **Error Handling**: Comprehensive error handling with logging

### Adding New Features

#### 1. Launcher System Features
Add new components to `core/launcher/`:
```python
# core/launcher/new_feature.py
from pathlib import Path
from typing import Dict, Any

class NewFeature:
    """New feature implementation."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data using new feature."""
        # Implementation here
        return {"result": "processed"}
```

#### 2. Web Interface Features
Add new endpoints to `web_app.py`:
```python
@app.post("/api/new-feature")
async def new_feature_endpoint(request: FeatureRequest):
    """Handle new feature requests."""
    try:
        result = process_new_feature(request.data)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"New feature error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 3. CLI Features
Add new commands to `main.py`:
```python
@click.command()
@click.option("--new-param", help="New parameter description")
def new_command(new_param: str):
    """New command description."""
    try:
        result = execute_new_command(new_param)
        click.echo(f"Success: {result}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
```

## 🔒 Security Guidelines

### Security Best Practices
1. **Input Validation**: Validate all user inputs
2. **Error Handling**: Don't expose sensitive information in errors
3. **Authentication**: Secure API key storage and handling
4. **Encryption**: Use strong encryption for sensitive data
5. **Logging**: Log security events without exposing secrets

### Security Review Checklist
- [ ] All user inputs validated and sanitized
- [ ] No hardcoded secrets or credentials
- [ ] Proper error handling without information disclosure
- [ ] Secure file handling with path validation
- [ ] Authentication and authorization implemented correctly
- [ ] Encryption used for sensitive data storage
- [ ] Security tests included

### Reporting Security Issues
Please report security vulnerabilities privately by emailing:
- Create a private GitHub issue marked as security
- Include detailed description and reproduction steps
- We will respond within 48 hours
- Public disclosure after fix is released

## 📚 Documentation Guidelines

### Documentation Types
1. **Code Documentation**: Docstrings and inline comments
2. **API Documentation**: Function and class documentation
3. **User Documentation**: Usage guides and tutorials
4. **Developer Documentation**: Architecture and contribution guides

### Writing Guidelines
- **Clear and Concise**: Use simple, direct language
- **Examples**: Include practical examples and code snippets
- **Up-to-date**: Keep documentation synchronized with code
- **Accessible**: Write for various skill levels
- **Searchable**: Use clear headings and keywords

### Documentation Updates
- Update relevant documentation with code changes
- Add new documentation for new features
- Include screenshots for UI changes
- Update API documentation for endpoint changes
- Verify all links and examples work

## 🐛 Bug Reports

### Before Reporting
1. **Search Existing Issues**: Check if bug already reported
2. **Try Latest Version**: Update to latest release
3. **Minimal Reproduction**: Create minimal example
4. **Environment Details**: Gather system information

### Bug Report Template
```markdown
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What you expected to happen

## Actual Behavior
What actually happened

## Environment
- OS: Windows 10 / Ubuntu 20.04 / macOS 12
- Python Version: 3.9.7
- Package Version: 3.0.0
- FAL API Key: [Present/Missing]

## Additional Context
Screenshots, logs, or other helpful information
```

## 💡 Feature Requests

### Feature Request Template
```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed? What problem does it solve?

## Proposed Solution
How should this feature work?

## Alternatives Considered
What alternatives have you considered?

## Additional Context
Mockups, examples, or related issues
```

## 🔄 Release Process

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 3.1.2)
- **Major**: Breaking changes
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, backward compatible

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers bumped
- [ ] Security review completed
- [ ] Performance benchmarks run
- [ ] Docker images built and tested

## 🏷️ Labels and Issues

### Issue Labels
- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements or additions to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `security`: Security-related issue
- `performance`: Performance-related issue
- `breaking-change`: Breaking change in next release

### Priority Labels
- `priority: critical`: Critical issues requiring immediate attention
- `priority: high`: High priority issues
- `priority: medium`: Medium priority issues
- `priority: low`: Low priority issues

## 🎉 Recognition

### Contributor Recognition
- Contributors are acknowledged in release notes
- Major contributors added to README.md
- Special recognition for security researchers
- Community contributors highlighted in changelog

### Hall of Fame
We maintain a contributors hall of fame recognizing:
- First-time contributors
- Most active contributors
- Security researchers
- Documentation contributors
- Community helpers

## 📞 Getting Help

### Community Support
- **GitHub Discussions**: General questions and discussions
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Check README.md and CLAUDE.md first

### Development Questions
- **Architecture**: Ask about design decisions and patterns
- **Testing**: Get help with test strategies and frameworks
- **Security**: Guidance on security best practices
- **Performance**: Optimization tips and profiling help

## 📋 Contributor License Agreement

By contributing to this project, you agree that:
1. Your contributions will be licensed under the MIT License
2. You have the right to submit the contribution
3. You understand the open source nature of the project
4. You grant us the right to use your contribution

---

Thank you for contributing to FAL.AI Video Generator CLI! Your contributions help make this project better for everyone. 🙏

**Questions?** Open a GitHub Discussion or issue - we're here to help! 🤝