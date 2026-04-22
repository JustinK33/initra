# Changelog

## [1.0.0] - Initial Release

### Features
- Initial release of newproj CLI
- Support for Python (Flask, FastAPI, Django)
- Support for Node.js (Express, Express + TypeScript, Next.js)
- Support for Ruby (Rails)
- Support for Java (Spring Boot)
- Automatic Python virtual environment creation
- GitHub repository integration with `--gh` flag
- VS Code launch with `--open` flag
- Interactive mode when run without arguments
- TypeScript support for Express projects with `--ts` flag
- Comprehensive documentation (README, INSTALL, USAGE, TESTING)
- Proper error handling and cross-platform compatibility

### Security
- Uses subprocess with safe parameter passing
- No shell injection vulnerabilities
- Proper error handling for missing dependencies
