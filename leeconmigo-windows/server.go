package main

import (
	"embed"
	"errors"
	"io/fs"
	"mime"
	"net"
	"net/http"
)

//go:embed all:www
var content embed.FS

func startServer() (string, error) {
	_ = mime.AddExtensionType(".mp3", "audio/mpeg")
	_ = mime.AddExtensionType(".jpg", "image/jpeg")
	_ = mime.AddExtensionType(".json", "application/json")
	sub, err := fs.Sub(content, "www")
	if err != nil {
		return "", err
	}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return "", err
	}
	go func() {
		_ = http.Serve(ln, http.FileServer(http.FS(sub)))
	}()
	return "http://" + ln.Addr().String() + "/", nil
}

func mustServer() string {
	url, err := startServer()
	if err != nil {
		panic(err)
	}
	if url == "" {
		panic(errors.New("servidor vacío"))
	}
	return url
}
