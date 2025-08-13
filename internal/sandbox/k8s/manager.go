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
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/wait"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"

	"github.com/woxqaq/simple-sandbox/internal/constants"
	"github.com/woxqaq/simple-sandbox/internal/models"
	"github.com/woxqaq/simple-sandbox/internal/sandbox/common"
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
				Name:       constants.K8sRunnerContainer,
				Image:      image,
				WorkingDir: constants.WorkspaceDir,
				Env:        []corev1.EnvVar{{Name: constants.SandboxEnvKey, Value: constants.SandboxEnvVal}},
				VolumeMounts: []corev1.VolumeMount{
					{Name: constants.K8sVolumeCode, MountPath: constants.WorkspaceDir, ReadOnly: true},
					{Name: constants.K8sVolumeTmp, MountPath: constants.TmpDir},
					{Name: constants.K8sVolumeDShm, MountPath: constants.DevShmDir},
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
