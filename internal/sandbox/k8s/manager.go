package k8s

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"io"
	"time"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/wait"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"

	"github.com/woxqaq/simple-sandbox/internal/constants"
	"github.com/woxqaq/simple-sandbox/internal/models"
	"github.com/woxqaq/simple-sandbox/internal/sandbox/common"
	seccomppkg "github.com/woxqaq/simple-sandbox/internal/security/seccomp"
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

func (m *Manager) Run(
	ctx context.Context,
	req *models.RunRequest,
) (*models.RunResult, error) {
	ns := req.Namespace

	k8sConfig := GetConfig()
	image := common.ImageFor(req.Language)
	pullSecret := k8sConfig.ImagePullSecret

	// Determine code key by language
	codeKey := common.CodeFilenameForLanguage(req.Language)

	suffix := randHex(6)
	cmName := constants.K8sConfigMapNamePref + suffix
	podName := constants.K8sPodNamePref + suffix
	seccompProfileName := constants.K8sSeccompProfilePref + suffix

	// Create seccomp profile config map
	seccompProfile := seccomppkg.For(req.Language)
	seccompCM := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{Name: seccompProfileName, Namespace: ns},
		Data:       map[string]string{"seccomp.json": seccompProfile},
	}
	if _, err := m.client.
		CoreV1().
		ConfigMaps(ns).
		Create(ctx, seccompCM, metav1.CreateOptions{}); err != nil {
		return nil, fmt.Errorf("create seccomp configmap: %w", err)
	}
	defer func() {
		_ = m.client.
			CoreV1().
			ConfigMaps(ns).
			Delete(context.Background(), seccompProfileName, metav1.DeleteOptions{})
	}()

	cm := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{Name: cmName, Namespace: ns},
		Data:       map[string]string{codeKey: req.Code},
	}
	if _, err := m.client.
		CoreV1().
		ConfigMaps(ns).
		Create(ctx, cm, metav1.CreateOptions{}); err != nil {
		return nil, fmt.Errorf("create configmap: %w", err)
	}
	defer func() {
		_ = m.client.
			CoreV1().
			ConfigMaps(ns).
			Delete(context.Background(), cmName, metav1.DeleteOptions{})
	}()

	// Pod with security context and seccomp profile; tmpfs-like /tmp via emptyDir memory
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
				Name:       constants.K8sRunnerContainer,
				Image:      image,
				WorkingDir: constants.WorkspaceDir,
				Env:        []corev1.EnvVar{{Name: constants.SandboxEnvKey, Value: constants.SandboxEnvVal}},
				VolumeMounts: []corev1.VolumeMount{
					{Name: constants.K8sVolumeCode, MountPath: constants.WorkspaceDir, ReadOnly: true},
					{Name: constants.K8sVolumeTmp, MountPath: constants.TmpDir},
					{Name: constants.K8sVolumeDShm, MountPath: constants.DevShmDir},
					{Name: constants.K8sVolumeSeccomp, MountPath: constants.SeccompProfilePath, ReadOnly: true},
				},
				SecurityContext: &corev1.SecurityContext{
					RunAsUser:    func(i int64) *int64 { return &i }(1000),
					RunAsGroup:   func(i int64) *int64 { return &i }(1000),
					ReadOnlyRootFilesystem: func(b bool) *bool { return &b }(true),
					Capabilities: &corev1.Capabilities{
						Drop: []corev1.Capability{"ALL"},
					},
					AllowPrivilegeEscalation: func(b bool) *bool { return &b }(false),
					SeccompProfile: &corev1.SeccompProfile{
						Type: corev1.SeccompProfileTypeLocalhost,
						LocalhostProfile: func(s string) *string { return &s }(constants.SeccompProfilePath),
					},
				},
				Resources: corev1.ResourceRequirements{
					Limits: corev1.ResourceList{
						"memory": func() resource.Quantity {
							q, _ := resource.ParseQuantity(fmt.Sprintf("%dMi", req.MemoryMB))
							return q
						}(),
						"cpu": func() resource.Quantity {
							q, _ := resource.ParseQuantity(fmt.Sprintf("%dm", req.CPUShares))
							return q
						}(),
					},
				},
			}},
			Volumes: []corev1.Volume{
				{
					Name: constants.K8sVolumeCode,
					VolumeSource: corev1.VolumeSource{
						ConfigMap: &corev1.ConfigMapVolumeSource{
							LocalObjectReference: corev1.LocalObjectReference{Name: cmName},
						},
					},
				},
				{
					Name: constants.K8sVolumeTmp,
					VolumeSource: corev1.VolumeSource{
						EmptyDir: &corev1.EmptyDirVolumeSource{Medium: corev1.StorageMediumMemory},
					},
				},
				{
					Name: constants.K8sVolumeDShm,
					VolumeSource: corev1.VolumeSource{
						EmptyDir: &corev1.EmptyDirVolumeSource{Medium: corev1.StorageMediumMemory},
					},
				},
				{
					Name: constants.K8sVolumeSeccomp,
					VolumeSource: corev1.VolumeSource{
						ConfigMap: &corev1.ConfigMapVolumeSource{
							LocalObjectReference: corev1.LocalObjectReference{Name: seccompProfileName},
							Items: []corev1.KeyToPath{
								{Key: "seccomp.json", Path: "seccomp.json"},
							},
						},
					},
				},
			},
		},
	}
	if _, err := m.client.
		CoreV1().
		Pods(ns).
		Create(ctx, pod, metav1.CreateOptions{}); err != nil {
		return nil, fmt.Errorf("create pod: %w", err)
	}
	defer func() {
		_ = m.client.
			CoreV1().
			Pods(ns).
			Delete(context.Background(), podName, metav1.DeleteOptions{})
	}()

	// record start time from pod creation to completion
	start := time.Now()
	deadline := time.Duration(req.TimeLimitMs+constants.TimeLimitGraceMs) * time.Millisecond
	ctxW, cancel := context.WithTimeout(ctx, deadline)
	defer cancel()
	// wait for completion
	err := wait.PollUntilContextCancel(ctxW, time.Duration(constants.K8sPollIntervalMs)*time.Millisecond, true, func(ctx context.Context) (done bool, err error) {
		p, err := m.client.
			CoreV1().
			Pods(ns).
			Get(ctx, podName, metav1.GetOptions{})
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
	reqLog := m.client.
		CoreV1().
		Pods(ns).
		GetLogs(podName, &corev1.PodLogOptions{
			Container: "runner",
		})
	stream, err := reqLog.Stream(context.Background())
	if err != nil {
		return nil, fmt.Errorf("pod logs: %w", err)
	}
	defer stream.Close()
	buf := new(bytes.Buffer)
	if _, err := io.Copy(buf, stream); err != nil {
		return nil, err
	}

	parsed, perr := common.ParseRunnerJSONFromBytes(buf.Bytes())
	if perr != nil {
		return &models.RunResult{
			ExitCode:   -1,
			Stdout:     buf.String(),
			DurationMs: int(time.Since(start).Milliseconds()),
		}, nil
	}
	return &models.RunResult{
		ExitCode:   parsed.ExitCode,
		Stdout:     parsed.Stdout,
		Stderr:     parsed.Stderr,
		Artifacts:  parsed.Artifacts,
		DurationMs: int(time.Since(start).Milliseconds()),
	}, nil
}

func randHex(n int) string {
	b := make([]byte, n)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}
