# Contributing to InfoBlox MCP Server

Thank you for your interest in contributing to the InfoBlox MCP Server! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues

Before creating an issue, please:

1. **Search existing issues** to avoid duplicates
2. **Use the issue templates** when available
3. **Provide detailed information** including:
   - InfoBlox NIOS version
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and logs

### Suggesting Features

We welcome feature suggestions! Please:

1. **Check existing feature requests** first
2. **Describe the use case** clearly
3. **Explain the expected behavior**
4. **Consider implementation complexity**

### Code Contributions

#### Getting Started

1. **Fork the repository**
2. **Clone your fork**:
   ```bash
   git clone https://github.com/yourusername/infoblox-mcp-server.git
   cd infoblox-mcp-server
   ```
3. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

#### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes**
3. **Run tests**:
   ```bash
   python3 test_server.py
   python3 comprehensive_test.py
   python3 integration_test.py
   ```
4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add: Brief description of your changes"
   ```
5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Create a Pull Request**

## 📝 Code Standards

### Python Style Guide

- Follow **PEP 8** style guidelines
- Use **type hints** where appropriate
- Write **docstrings** for all functions and classes
- Keep line length under **100 characters**
- Use **meaningful variable names**

### Code Structure

```python
"""Module docstring describing the purpose."""

import standard_library_imports
import third_party_imports
from local_imports import LocalClass

# Constants
CONSTANT_VALUE = "value"

class ExampleClass:
    """Class docstring."""
    
    def __init__(self, param: str):
        """Initialize with parameter."""
        self.param = param
    
    def method_name(self, arg: int) -> str:
        """Method docstring describing purpose and parameters."""
        return f"Result: {arg}"

async def async_function(param: str) -> dict:
    """Async function docstring."""
    try:
        result = await some_operation(param)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error in async_function: {str(e)}")
        raise
```

### Tool Development Guidelines

When adding new InfoBlox tools:

1. **Follow naming convention**: `infoblox_{category}_{action}`
2. **Use appropriate module**: Add to `dns_tools.py`, `dhcp_tools.py`, etc.
3. **Include comprehensive schema**:
   ```python
   {
       "type": "object",
       "properties": {
           "parameter_name": {
               "type": "string",
               "description": "Clear description of the parameter"
           }
       },
       "required": ["required_parameter"]
   }
   ```
4. **Implement error handling**:
   ```python
   async def _tool_handler(self, args: Dict[str, Any], client: InfoBloxClient) -> str:
       try:
           # Validate inputs
           # Call InfoBlox API
           # Return JSON response
           return json.dumps(result, indent=2)
       except Exception as e:
           logger.error(f"Error in tool: {str(e)}")
           raise InfoBloxAPIError(f"Tool failed: {str(e)}")
   ```

### Testing Requirements

All contributions must include tests:

1. **Unit tests** for new functions
2. **Integration tests** for new tools
3. **Mock tests** for InfoBlox API interactions
4. **Documentation tests** for examples

Example test structure:
```python
async def test_new_tool():
    """Test new tool functionality."""
    registry = ToolRegistry()
    
    # Test with valid inputs
    result = await registry.execute_tool("tool_name", valid_args, mock_client)
    assert "success" in result
    
    # Test with invalid inputs
    with pytest.raises(ValidationError):
        await registry.execute_tool("tool_name", invalid_args, mock_client)
```

## 📚 Documentation

### Documentation Requirements

- **Update README.md** if adding new features
- **Update DOCUMENTATION.md** with detailed usage
- **Add examples** to `examples.py`
- **Update tool inventory** if adding tools
- **Include inline documentation** with docstrings

### Documentation Style

- Use **clear, concise language**
- Include **practical examples**
- Provide **error handling guidance**
- Use **consistent formatting**

## 🧪 Testing

### Running Tests

```bash
# Basic functionality
python3 test_server.py

# Comprehensive tests
python3 comprehensive_test.py

# Integration tests
python3 integration_test.py

# Performance tests
python3 -m pytest tests/ -v
```

### Test Coverage

Aim for **80%+ test coverage** on new code:

```bash
# Install coverage tools
pip install coverage pytest

# Run with coverage
coverage run -m pytest tests/
coverage report
coverage html  # Generate HTML report
```

## 🔍 Code Review Process

### Pull Request Guidelines

1. **Clear title and description**
2. **Reference related issues**
3. **Include test results**
4. **Update documentation**
5. **Follow commit message format**:
   - `Add: New feature or functionality`
   - `Fix: Bug fix`
   - `Update: Modification to existing feature`
   - `Docs: Documentation changes`
   - `Test: Test-related changes`

### Review Criteria

Pull requests will be reviewed for:

- **Code quality and style**
- **Test coverage**
- **Documentation completeness**
- **Performance impact**
- **Security considerations**
- **Backward compatibility**

## 🚀 Release Process

### Version Numbering

We follow **Semantic Versioning** (SemVer):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `pyproject.toml`
- [ ] Git tag created
- [ ] Release notes prepared

## 🛡️ Security

### Security Guidelines

- **Never commit credentials** or sensitive data
- **Validate all inputs** thoroughly
- **Use secure communication** (HTTPS/TLS)
- **Follow security best practices**
- **Report security issues** privately

### Reporting Security Issues

Please report security vulnerabilities to:
- **Email**: security@yourproject.com
- **Use GitHub Security Advisories** for coordinated disclosure

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Documentation**: Check existing docs first
- **Code Comments**: For implementation questions

### Development Environment

If you need help setting up your development environment:

1. **Check the installation guide**
2. **Review common issues** in documentation
3. **Ask in GitHub Discussions**
4. **Include environment details** when asking for help

## 🎉 Recognition

Contributors will be recognized in:

- **CONTRIBUTORS.md** file
- **Release notes**
- **GitHub contributors page**
- **Special mentions** for significant contributions

Thank you for contributing to the InfoBlox MCP Server! Your contributions help make this tool better for everyone.

