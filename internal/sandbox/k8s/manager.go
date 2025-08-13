package k8s

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"time"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/wait"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"

	"github.com/woxqaq/simple-sandbox/internal/models"
)

type Manager struct {
	client    *kubernetes.Clientset
	namespace string
}

func New() (*Manager, error) {
	var cfg *rest.Config
	var err error
	if c, errIn := rest.InClusterConfig(); errIn == nil {
		cfg = c
	} else {
		cfg, err = clientcmd.BuildConfigFromFlags("", clientcmd.RecommendedHomeFile)
		if err != nil {
			return nil, err
		}
	}
	cs, err := kubernetes.NewForConfig(cfg)
	if err != nil {
		return nil, err
	}
	return &Manager{client: cs, namespace: "default"}, nil
}

type runnerJSON struct {
	Stdout    string   `json:"stdout"`
	Stderr    string   `json:"stderr"`
	ImagesB64 []string `json:"images_b64"`
	ExitCode  int      `json:"exit_code"`
}

func (m *Manager) Run(ctx context.Context, req *models.RunRequest) (*models.RunResult, error) {
	if err := req.Validate(); err != nil {
		return nil, err
	}

	ns := req.Namespace

	k8sConfig := GetConfig()
	image := k8sConfig.ImageFor(req.Language)
	pullSecret := k8sConfig.K8sImagePullSecret()

	// Determine code key by language
	codeKey := "main"
	switch req.Language {
	case models.LanguagePython:
		codeKey = "main.py"
	case models.LanguageNode:
		codeKey = "main.js"
	}

	suffix := randHex(6)
	cmName := "sb-code-" + suffix
	podName := "sb-pod-" + suffix

	cm := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{Name: cmName, Namespace: ns},
		Data:       map[string]string{codeKey: req.Code},
	}
	if _, err := m.client.CoreV1().ConfigMaps(ns).Create(ctx, cm, metav1.CreateOptions{}); err != nil {
		return nil, fmt.Errorf("create configmap: %w", err)
	}
	defer func() {
		_ = m.client.CoreV1().ConfigMaps(ns).Delete(context.Background(), cmName, metav1.DeleteOptions{})
	}()

	// Pod with default securityContext; tmpfs-like /tmp via emptyDir memory
	pod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{Name: podName, Namespace: ns},
		Spec: corev1.PodSpec{
			RestartPolicy:                corev1.RestartPolicyNever,
			AutomountServiceAccountToken: func(b bool) *bool { return &b }(false),
			ImagePullSecrets: func() []corev1.LocalObjectReference {
				if pullSecret == "" {
					return nil
				}
				return []corev1.LocalObjectReference{{Name: pullSecret}}
			}(),
			Containers: []corev1.Container{{
				Name:       "runner",
				Image:      image,
				WorkingDir: "/workspace",
				Env:        []corev1.EnvVar{{Name: "SANDBOX", Value: "1"}},
				VolumeMounts: []corev1.VolumeMount{
					{Name: "code", MountPath: "/workspace", ReadOnly: true},
					{Name: "tmp", MountPath: "/tmp"},
					{Name: "dshm", MountPath: "/dev/shm"},
				},
			}},
			Volumes: []corev1.Volume{
				{Name: "code", VolumeSource: corev1.VolumeSource{ConfigMap: &corev1.ConfigMapVolumeSource{LocalObjectReference: corev1.LocalObjectReference{Name: cmName}}}},
				{Name: "tmp", VolumeSource: corev1.VolumeSource{EmptyDir: &corev1.EmptyDirVolumeSource{Medium: corev1.StorageMediumMemory}}},
				{Name: "dshm", VolumeSource: corev1.VolumeSource{EmptyDir: &corev1.EmptyDirVolumeSource{Medium: corev1.StorageMediumMemory}}},
			},
		},
	}
	if _, err := m.client.CoreV1().Pods(ns).Create(ctx, pod, metav1.CreateOptions{}); err != nil {
		return nil, fmt.Errorf("create pod: %w", err)
	}
	defer func() {
		_ = m.client.CoreV1().Pods(ns).Delete(context.Background(), podName, metav1.DeleteOptions{})
	}()

	deadline := time.Duration(req.TimeLimitMs+2000) * time.Millisecond
	ctxW, cancel := context.WithTimeout(ctx, deadline)
	defer cancel()
	// wait for completion
	err := wait.PollUntilContextCancel(ctxW, 500*time.Millisecond, true, func(ctx context.Context) (done bool, err error) {
		p, err := m.client.CoreV1().Pods(ns).Get(ctx, podName, metav1.GetOptions{})
		if err != nil {
			return false, nil
		}
		s := p.Status.Phase
		if s == corev1.PodSucceeded || s == corev1.PodFailed {
			return true, nil
		}
		return false, nil
	})
	if err != nil && ctxW.Err() != nil {
		return nil, ctxW.Err()
	}

	// fetch logs
	reqLog := m.client.CoreV1().Pods(ns).GetLogs(podName, &corev1.PodLogOptions{Container: "runner"})
	stream, err := reqLog.Stream(context.Background())
	if err != nil {
		return nil, fmt.Errorf("pod logs: %w", err)
	}
	defer stream.Close()
	buf := new(bytes.Buffer)
	if _, err := io.Copy(buf, stream); err != nil {
		return nil, err
	}

	var r runnerJSON
	idx := bytes.LastIndexByte(buf.Bytes(), '{')
	if idx >= 0 {
		_ = json.Unmarshal(buf.Bytes()[idx:], &r)
	}
	return &models.RunResult{ExitCode: r.ExitCode, Stdout: r.Stdout, Stderr: r.Stderr, ImagesB64: r.ImagesB64}, nil
}

func randHex(n int) string {
	b := make([]byte, n)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}
