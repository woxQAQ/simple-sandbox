package utils

import (
	"fmt"

	. "github.com/onsi/gomega"
	"github.com/woxqaq/simple-sandbox/internal/models"
)

// AssertArtifactExists 断言 artifact 存在
func AssertArtifactExists(artifacts []models.Artifact, artifactType string) {
	found := false
	for _, artifact := range artifacts {
		if artifact.Type == artifactType {
			found = true
			break
		}
	}
	Expect(found).To(BeTrue(), fmt.Sprintf("Expected artifact of type %s to exist", artifactType))
}

// AssertArtifactCount 断言 artifact 数量
func AssertArtifactCount(artifacts []models.Artifact, artifactType string, expectedCount int) {
	count := 0
	for _, artifact := range artifacts {
		if artifact.Type == artifactType {
			count++
		}
	}
	Expect(count).To(Equal(expectedCount), fmt.Sprintf("Expected %d artifacts of type %s, got %d", expectedCount, artifactType, count))
}