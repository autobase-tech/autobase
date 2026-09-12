//go:build swagger

package main

// Keep dependencies imported only by generated Swagger code in go.mod.
// The swagger build tag lets go mod tidy discover them without adding them to the application binary.
import (
	_ "github.com/go-openapi/spec"
	_ "github.com/go-openapi/swag/cmdutils"
	_ "github.com/go-openapi/swag/conv"
	_ "github.com/go-openapi/swag/jsonutils"
	_ "github.com/go-openapi/swag/netutils"
	_ "github.com/go-openapi/swag/typeutils"
	_ "github.com/go-openapi/validate"
	_ "golang.org/x/net/netutil"
)
