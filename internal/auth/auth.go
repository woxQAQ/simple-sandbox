package auth

import (
	"errors"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
)

var (
	ErrUnauthorized = errors.New("unauthorized")
	ErrInvalidToken = errors.New("invalid token")
)

// JWTClaims 自定义 JWT 声明
type JWTClaims struct {
	UserID string `json:"user_id"`
	Role   string `json:"role"`
	jwt.RegisteredClaims
}

// AuthManager JWT 认证管理器
type AuthManager struct {
	secretKey    []byte
	tokenTTL    time.Duration
	issuer      string
}

// NewAuthManager 创建新的 JWT 认证管理器
func NewAuthManager(secretKey string, tokenTTL time.Duration) *AuthManager {
	return &AuthManager{
		secretKey: []byte(secretKey),
		tokenTTL: tokenTTL,
		issuer:   "simple-sandbox",
	}
}

// GenerateToken 生成 JWT 令牌
func (am *AuthManager) GenerateToken() (string, error) {
	claims := JWTClaims{
		UserID: "sandbox-user",
		Role:   "user",
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(am.tokenTTL)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			Issuer:    am.issuer,
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(am.secretKey)
}

// ValidateToken 验证 JWT 令牌
func (am *AuthManager) ValidateToken(tokenString string) (*JWTClaims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &JWTClaims{}, func(token *jwt.Token) (interface{}, error) {
		return am.secretKey, nil
	})

	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(*JWTClaims); ok && token.Valid {
		return claims, nil
	}

	return nil, ErrInvalidToken
}

// Middleware 创建 Gin 认证中间件
func (am *AuthManager) Middleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header required"})
			c.Abort()
			return
		}

		tokenString := authHeader[len("Bearer "):]
		if len(tokenString) == len(authHeader) {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid authorization format"})
			c.Abort()
			return
		}

		claims, err := am.ValidateToken(tokenString)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid or expired token"})
			c.Abort()
			return
		}

		// 将用户信息存储在上下文中
		c.Set("user_id", claims.UserID)
		c.Set("user_role", claims.Role)
		c.Next()
	}
}

// GetCurrentUser 从上下文获取当前用户信息
func GetCurrentUser(c *gin.Context) (string, string) {
	userID, _ := c.Get("user_id")
	role, _ := c.Get("user_role")
	return userID.(string), role.(string)
}