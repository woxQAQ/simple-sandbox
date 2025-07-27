# Security Architecture

## Overview

This document describes the security architecture implemented in the simple-sandbox project. The security system provides comprehensive protection for executing untrusted code through seccomp (secure computing mode) system call filtering, privilege separation, and resource isolation.

## Architecture Components

### 1. System Call Configuration (`src/security/syscalls/`)

- **Purpose**: Manages allowed system calls for different programming languages
- **Key Files**:
  - `parser.py`: Parses JSON configuration files for each language
  - Configuration files in `build/seccomp/`: Language-specific syscall allowlists

### 2. Seccomp Injection (`src/security/bpf/`)

- **Purpose**: Implements runtime seccomp filter injection
- **Key Files**:
  - `seccomp_injector.c`: C implementation of seccomp BPF program generation
  - `seccomp_injector.h`: Header file with function declarations
  - `Makefile`: Build configuration for shared library

### 3. Python Integration (`src/security/injection/`)

- **Purpose**: Python wrapper for C seccomp functionality
- **Key Files**:
  - `seccomp_wrapper.py`: Python ctypes interface to C library

### 4. Security Manager (`src/security/__init__.py`)

- **Purpose**: Unified interface for security operations
- **Features**:
  - Language-specific security profile management
  - Seccomp filter application
  - Privilege dropping

## Security Workflow

The security system implements a three-stage workflow:

### Stage 1: Prevent Privilege Escalation
```c
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)
```
- Prevents the process from gaining new privileges
- Must be set before applying seccomp filters

### Stage 2: Apply Seccomp Filter
```c
prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &bpf_program)
```
- Loads BPF program that filters system calls
- Only allows predefined syscalls for the specific language
- Blocks dangerous operations (network, file system, process creation)

### Stage 3: Drop Privileges
```c
setgid(sandbox_gid);
setuid(sandbox_uid);
```
- Drops to unprivileged user (typically `nobody:nobody`)
- Ensures the process cannot access sensitive resources

## Supported Platforms

- **Linux**: Full seccomp support (amd64, arm64)
- **macOS**: Stub implementation (seccomp not available)
- **Other platforms**: Not supported

## Language Support

Currently supported languages with predefined syscall profiles:

- **Python**: Optimized for Python runtime requirements
- **Node.js**: Tailored for JavaScript/Node.js execution
- **Extensible**: Easy to add new languages by creating JSON configurations

## Integration with Runtime Manager

The security system is integrated into the `ProcessManager` class:

```python
from src.runtime.manager import ProcessManager

# Create manager with seccomp enabled
manager = ProcessManager(enable_seccomp=True)

# Execute code with security profile
result = manager.execute_process(
    command=["python3", "-c", "print('Hello, secure world!')"],
    timeout=10,
    memory_limit=128,
    language="python",
    sandbox_uid=65534,  # nobody
    sandbox_gid=65534,  # nobody
)
```

## Build and Installation

### Quick Start
```bash
# Build all security components
make build-security

# Run tests
make test-security

# Install to system (Linux only, requires sudo)
make install-security
```

### Manual Build
```bash
# Build shared library
cd src/security/bpf
make

# Or use the build script
./build_security.sh
```

### Docker Build
```bash
# Build security-enabled Docker image
make docker-security
```

## Configuration

### Adding New Languages

1. Create a new JSON file in `build/seccomp/`:
```json
{
  "language": "ruby",
  "syscalls": [
    "read", "write", "open", "close",
    "mmap", "munmap", "brk",
    "rt_sigaction", "rt_sigprocmask",
    "exit_group"
  ]
}
```

2. The system will automatically detect and load the configuration

### Customizing Syscall Lists

Edit the JSON files in `build/seccomp/` to modify allowed syscalls:

- **Add syscalls**: Include additional syscall names in the array
- **Remove syscalls**: Remove syscall names (be careful not to break basic functionality)
- **Validate**: Use `make test-security` to verify configurations

## Security Considerations

### Threat Model

The security system protects against:

- **System call abuse**: Blocks dangerous syscalls (network, file access, process creation)
- **Privilege escalation**: Prevents gaining additional privileges
- **Resource exhaustion**: Combined with resource limits (memory, CPU, file size)
- **Container escape**: Additional layer beyond Docker security

### Limitations

- **Kernel vulnerabilities**: Cannot protect against kernel-level exploits
- **Side-channel attacks**: No protection against timing or cache attacks
- **Resource limits**: Seccomp doesn't enforce resource limits (handled separately)

### Best Practices

1. **Defense in depth**: Use seccomp alongside other security measures
2. **Minimal privileges**: Run with the least privileged user possible
3. **Regular updates**: Keep syscall configurations updated
4. **Monitoring**: Log and monitor seccomp violations
5. **Testing**: Regularly test security configurations

## Troubleshooting

### Common Issues

1. **Library not found**:
   ```
   Error: Failed to load library libseccomp_injector.so
   ```
   Solution: Run `make build-security` or check library path

2. **Seccomp not supported**:
   ```
   Warning: Seccomp not available, running without syscall filtering
   ```
   Solution: This is expected on non-Linux platforms

3. **Permission denied**:
   ```
   Error: Failed to apply seccomp profile
   ```
   Solution: Ensure proper privileges and kernel support

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Security

Run the security demonstration:
```bash
python3 examples/secure_execution_example.py
```

## Performance Impact

Seccomp filtering has minimal performance overhead:

- **Syscall filtering**: ~1-5% overhead per system call
- **BPF program**: Executed in kernel space, very fast
- **Memory usage**: Negligible additional memory consumption

## Future Enhancements

- **Dynamic syscall learning**: Automatically generate syscall profiles
- **Advanced BPF programs**: Argument-based filtering
- **Integration with audit**: Log seccomp violations
- **Performance monitoring**: Track security overhead
- **Additional architectures**: Support for more CPU architectures

## References

- [Linux seccomp documentation](https://www.kernel.org/doc/Documentation/prctl/seccomp_filter.txt)
- [BPF documentation](https://www.kernel.org/doc/html/latest/networking/filter.html)
- [Docker seccomp profiles](https://docs.docker.com/engine/security/seccomp/)