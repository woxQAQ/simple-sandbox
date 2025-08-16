package testdata

import (
	"embed"
	"strings"
)

//go:embed python/basic/*.py
//go:embed python/runtime/*.py
//go:embed python/api/*.py
//go:embed python/security/*.py
//go:embed python/features/*.py
var pythonFS embed.FS

//go:embed node/basic/*.js
//go:embed node/runtime/*.js
//go:embed node/security/*.js
//go:embed node/features/*.js
var nodeFS embed.FS

// PythonCodes 包含各种 Python 测试代码
var PythonCodes = map[string]string{
	// ===== 基础功能测试 =====
	"hello_world":         readFile("python/basic/hello_world.py"),
	"simple_math":         readFile("python/basic/simple_math.py"),
	"basic_functionality": readFile("python/basic/basic_functionality.py"),

	// ===== 运行时测试 =====
	"import_test":         readFile("python/runtime/import_test.py"),
	"exception_handling":  readFile("python/runtime/exception_handling.py"),
	"numpy_operations":    readFile("python/runtime/numpy_operations.py"),

	// ===== API 测试 =====
	"task_status_transition": readFile("python/api/task_status_transition.py"),
	"task_cancellation":     readFile("python/api/task_cancellation.py"),

	// ===== 安全测试 =====
	"dangerous_directory_access":  readFile("python/security/dangerous_directory_access.py"),
	"network_protocol_test":      readFile("python/security/network_protocol_test.py"),
	"dangerous_system_operations": readFile("python/security/dangerous_system_operations.py"),
	"user_permission_test":       readFile("python/security/user_permission_test.py"),
	"container_escape_test":      readFile("python/security/container_escape_test.py"),

	
	// ===== 特定功能测试 =====
	"matplotlib_plot":  readFile("python/features/matplotlib_plot.py"),
	"error_code":       readFile("python/features/error_code.py"),
	"infinite_loop":    readFile("python/features/infinite_loop.py"),
	"memory_intensive": readFile("python/features/memory_intensive.py"),
	"file_operations":  readFile("python/features/file_operations.py"),
	"network_test":     readFile("python/features/network_test.py"),
	"system_calls":    readFile("python/features/system_calls.py"),
}

// NodeCodes 包含各种 Node.js 测试代码
var NodeCodes = map[string]string{
	// ===== 基础功能测试 =====
	"hello_world":         readFile("node/basic/hello_world.js"),
	"simple_math":         readFile("node/basic/simple_math.js"),
	"basic_functionality": readFile("node/basic/basic_functionality.js"),

	// ===== 运行时测试 =====
	"module_loading":   readFile("node/runtime/module_loading.js"),
	"error_handling":   readFile("node/runtime/error_handling.js"),
	"promise_test":     readFile("node/runtime/promise_test.js"),
	"empty_artifacts":  readFile("node/runtime/empty_artifacts.js"),

	// ===== 安全测试 =====
	"user_permission_test": readFile("node/security/user_permission_test.js"),

	// ===== 特定功能测试 =====
	"async_code":        readFile("node/features/async_code.js"),
	"error_code":        readFile("node/features/error_code.js"),
	"infinite_loop":     readFile("node/features/infinite_loop.js"),
	"memory_intensive":  readFile("node/features/memory_intensive.js"),
	"file_operations":  readFile("node/features/file_operations.js"),
	"network_test":     readFile("node/features/network_test.js"),
	"system_calls":    readFile("node/features/system_calls.js"),
}

// readFile 从嵌入的文件系统中读取文件内容
func readFile(path string) string {
	// 根据文件扩展名确定使用哪个文件系统
	var fs embed.FS
	if strings.HasSuffix(path, ".py") {
		fs = pythonFS
	} else if strings.HasSuffix(path, ".js") {
		fs = nodeFS
	} else {
		return ""
	}

	content, err := fs.ReadFile(path)
	if err != nil {
		// 如果文件不存在，返回空字符串
		return ""
	}
	return string(content)
}

// GetPythonCode 获取指定名称的 Python 测试代码
func GetPythonCode(name string) string {
	return PythonCodes[name]
}

// GetNodeCode 获取指定名称的 Node.js 测试代码
func GetNodeCode(name string) string {
	return NodeCodes[name]
}

// ListPythonCodes 列出所有可用的 Python 测试代码
func ListPythonCodes() []string {
	var codes []string
	for code := range PythonCodes {
		codes = append(codes, code)
	}
	return codes
}

// ListNodeCodes 列出所有可用的 Node.js 测试代码
func ListNodeCodes() []string {
	var codes []string
	for code := range NodeCodes {
		codes = append(codes, code)
	}
	return codes
}

// ExpectedOutputs 包含预期的输出结果
var ExpectedOutputs = map[string]map[string]interface{}{
	"python_hello_world": {
		"stdout":    "Hello, World!\n",
		"stderr":    "",
		"exit_code": 0,
	},
	"python_simple_math": {
		"stdout":    "2 + 3 = 5\n",
		"stderr":    "",
		"exit_code": 0,
	},
	"python_error_code": {
		"stdout":    "Before error\n",
		"exit_code": 1,
	},
	"node_hello_world": {
		"stdout":    "Hello, World!\n",
		"stderr":    "",
		"exit_code": 0,
	},
	"node_simple_math": {
		"stdout":    "2 + 3 = 5\n",
		"stderr":    "",
		"exit_code": 0,
	},
	"node_error_code": {
		"stdout":    "Before error\n",
		"exit_code": 1,
	},
}