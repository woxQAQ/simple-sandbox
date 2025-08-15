package e2e_test

import (
	"testing"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/woxqaq/simple-sandbox/e2e/utils"
)

var (
	globalTestServer *utils.TestServer
	globalHTTPClient *utils.HTTPClient
)

func TestE2E(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Simple Sandbox E2E Suite")
}

var _ = BeforeSuite(func() {
	// 全局测试设置
	By("Setting up test environment")
	
	// 启动全局测试服务器
	globalTestServer = utils.NewTestServer("8081")
	err := globalTestServer.Start()
	Expect(err).NotTo(HaveOccurred(), "Failed to start global test server")
	
	// 创建全局HTTP客户端
	globalHTTPClient = utils.NewHTTPClient(globalTestServer.GetBaseURL())
	
	By("Global test server started successfully")
})

var _ = AfterSuite(func() {
	// 全局测试清理
	By("Cleaning up test environment")
	
	if globalTestServer != nil {
		err := globalTestServer.Stop()
		Expect(err).NotTo(HaveOccurred(), "Failed to stop global test server")
	}
	
	By("Global test server stopped successfully")
})