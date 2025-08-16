package e2e_test

import (
	"sync"
	"testing"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/woxqaq/simple-sandbox/e2e/utils"
)

var (
	testServers      = make(map[int]*utils.TestServer)
	testServersMutex sync.Mutex
	serverCounter    int
)

func TestE2E(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Simple Sandbox E2E Suite")
}

// CreateParallelTestServer 为并行测试创建独立的服务器实例
func CreateParallelTestServer() (*utils.TestServer, *utils.HTTPClient, error) {
	testServersMutex.Lock()
	defer testServersMutex.Unlock()

	// 创建动态端口的服务器
	server, err := utils.CreateTestServerWithDynamicPort()
	if err != nil {
		return nil, nil, err
	}

	// 启动服务器
	err = server.Start()
	if err != nil {
		return nil, nil, err
	}

	// 创建HTTP客户端
	client := utils.NewHTTPClient(server.GetBaseURL())

	// 存储服务器引用以便清理
	serverCounter++
	testServers[serverCounter] = server

	return server, client, nil
}

// ReleaseParallelTestServer 释放并行测试服务器
func ReleaseParallelTestServer(server *utils.TestServer) error {
	testServersMutex.Lock()
	defer testServersMutex.Unlock()

	// 从映射中移除
	for id, s := range testServers {
		if s == server {
			delete(testServers, id)
			break
		}
	}

	return utils.ReleaseTestServer(server)
}

var _ = BeforeSuite(func() {
	// 预构建测试服务器二进制文件以避免重复构建
	By("Pre-building test server binary")
	buildCmd := utils.NewBuildCommand()
	err := buildCmd.Run()
	Expect(err).NotTo(HaveOccurred(), "Failed to pre-build server binary")

	By("Test environment setup completed")
})

var _ = AfterSuite(func() {
	// 清理所有剩余的测试服务器
	By("Cleaning up all test servers")

	testServersMutex.Lock()
	defer testServersMutex.Unlock()

	for _, server := range testServers {
		if server != nil {
			err := server.Stop()
			Expect(err).NotTo(HaveOccurred(), "Failed to stop test server")
		}
	}
	testServers = make(map[int]*utils.TestServer)

	By("All test servers cleaned up")
})
