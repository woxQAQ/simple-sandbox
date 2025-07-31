# Code Sandbox

A secure code execution sandbox with multi-language support.

## Features

- 🔒 **Secure Execution**: seccomp-based system call filtering for process-level security isolation
- 🐍 **Python Support**: Complete Python code execution environment
- 🟨 **Node.js Support**: Node.js code execution environment
- 🐳 **Containerized**: Multi-stage Docker build with comprehensive security configuration
- ☸️ **Kubernetes**: Helm chart support for cluster deployment
- 🧪 **Comprehensive Testing**: Unit tests, integration tests, and security tests
- 📊 **API Interface**: RESTful API with health checks and code execution
- 🔧 **Easy Deployment**: Multiple deployment methods with simple configuration

## Quick Start

### Local Development

```bash
# Clone project
git clone <repository-url>
cd sandbox

# Install dependencies
uv sync

# Start server
python main.py --port 8000 --verbose
```

### Docker Deployment

```bash
# Build image
docker build -t code-sandbox .

# Run container
docker run -p 8000:8000 code-sandbox
```

### Kubernetes Deployment

```bash
# Deploy using Helm chart
cd deploy/helm/sandbox
helm install my-sandbox . -f values.yaml
```

## API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### Code Execution
```bash
POST /api/v1/execute
Content-Type: application/json

{
  "language": "python",
  "code": "print('Hello, World!')"
}
```

## Supported Languages

- **Python 3.11**: Complete Python execution environment with standard library support
- **Node.js v20.11**: Node.js execution environment with npm package support

## Security Features

### System Call Filtering
- seccomp-based filtering of dangerous system calls
- Predefined security policy configurations
- BPF filter rule support

### Container Security
- Read-only root filesystem
- Non-root user execution
- Capability restrictions (drop ALL capabilities)
- Security context configuration

### Network Policy
- Default egress traffic restrictions
- Custom network policy configuration support
- Only allows necessary DNS and Kubernetes API access

## Configuration Options

### Command Line Arguments
```bash
python main.py [OPTIONS]

Options:
  -p, --port PORT    Listen port (default: 8000)
  --host HOST        Listen address (default: 0.0.0.0)
  -v, --verbose      Enable verbose logging
  --debug            Enable debug mode
```

### Environment Variables
- `HOST`: Server listen address
- `PORT`: Server listen port
- `DEBUG`: Debug mode
- `VERBOSE`: Verbose logging

## Project Structure

```
sandbox/
├── main.py                    # Main program entry
├── src/
│   ├── api/                   # API server
│   │   └── app.py            # HTTP server implementation
│   ├── runtime/              # Code runtime
│   │   ├── base.py           # Runtime base class
│   │   ├── python_runtime.py # Python runtime
│   │   ├── nodejs_runtime.py # Node.js runtime
│   │   └── manager.py        # Process manager
│   ├── security/             # Security module
│   │   ├── seccomp_wrapper.py # seccomp wrapper
│   │   └── static/           # Static security config
│   └── utils/                # Utility modules
├── deploy/helm/sandbox/      # Kubernetes Helm chart
├── tests/                    # Test files
└── docker/                   # Docker related files
```

## Development

### Install Development Dependencies
```bash
uv sync --group dev
```

### Run Tests
```bash
pytest
```

### Code Formatting
```bash
black src/
isort src/
ruff check src/
```

### Type Checking
```bash
mypy src/
```

## Deployment

### Production Environment
1. Build image using provided Dockerfile
2. Configure appropriate resource limits
3. Deploy to Kubernetes using Helm chart
4. Configure network policies and security groups

### Important Notes
- Enable resource limits in production environments
- Regularly update base images and security patches
- Monitor container resource usage
- Configure appropriate log collection

## License

[Please add license information here]

## Contributing

Issues and Pull Requests are welcome!

## Support

For questions, please submit an Issue or contact the development team.
