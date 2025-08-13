package e2e_test

import (
	"testing"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
)

func TestE2E(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Simple Sandbox E2E Suite")
}

var _ = BeforeSuite(func() {
	// 全局测试设置
	By("Setting up test environment")
	// 这里可以添加全局的测试环境设置
})

var _ = AfterSuite(func() {
	// 全局测试清理
	By("Cleaning up test environment")
	// 这里可以添加全局的测试环境清理
})