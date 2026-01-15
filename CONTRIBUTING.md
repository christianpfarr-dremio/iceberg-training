# Contributing to Apache Iceberg Training Setup

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## 🤝 How to Contribute

### Reporting Issues

If you encounter any problems:

1. **Check existing issues** to avoid duplicates
2. **Create a new issue** with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Docker version)
   - Relevant logs

### Suggesting Enhancements

We welcome suggestions for improvements:

1. **Open an issue** describing your enhancement
2. Explain the use case and benefits
3. Provide examples if possible

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Test thoroughly**:
   ```bash
   docker-compose down -v
   docker-compose up -d
   # Verify all services work
   ```
5. **Commit with clear messages**:
   ```bash
   git commit -m "Add feature: description"
   ```
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Open a Pull Request**

## 📝 Coding Standards

### Docker Compose

- Use meaningful service names
- Add comments for complex configurations
- Include health checks where applicable
- Document all environment variables
- Use resource limits for production setups

### Documentation

- Update README.md for user-facing changes
- Keep documentation clear and concise
- Include examples where helpful
- Update troubleshooting section if needed

### Commit Messages

Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

Example:
```
feat: add health checks to all services

- Add health check for Nessie API
- Add health check for MinIO
- Add health check for Dremio
- Update documentation
```

## 🧪 Testing

Before submitting a PR:

1. **Clean start test**:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

2. **Verify all services start**:
   ```bash
   docker-compose ps
   docker-compose logs
   ```

3. **Test persistence**:
   ```bash
   # Create data in Dremio
   docker-compose restart
   # Verify data persists
   ```

4. **Test documentation**:
   - Follow your own instructions
   - Verify all commands work
   - Check all links

## 🔒 Security

- **Never commit credentials** or secrets
- Use `.env.example` for configuration templates
- Report security issues privately
- Follow security best practices

## 📄 License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## ❓ Questions?

Feel free to open an issue for questions or reach out to the maintainers.

## 🙏 Thank You!

Your contributions help make this project better for everyone!

