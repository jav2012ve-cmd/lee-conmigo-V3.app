package main

import (
	"embed"
	"io/fs"
	"mime"
	"net"
	"net/http"
)

//go:embed all:www
var content embed.FS

func startServer() string {
	_ = mime.AddExtensionType(".mp3", "audio/mpeg")
	_ = mime.AddExtensionType(".png", "image/png")
	sub, err := fs.Sub(content, "www")
	if err != nil {
		panic(err)
	}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		panic(err)
	}
	go func() { _ = http.Serve(ln, http.FileServer(http.FS(sub))) }()
	return "http://" + ln.Addr().String() + "/"
}
