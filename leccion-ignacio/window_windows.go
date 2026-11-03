//go:build windows

package main

import (
	"os"
	"path/filepath"
	"unsafe"

	"github.com/jchv/go-webview2"
	"golang.org/x/sys/windows"
)

func main() {
	url := startServer()
	dataPath := filepath.Join(os.TempDir(), "LeccionIgnacio")
	w := webview2.NewWithOptions(webview2.WebViewOptions{
		Debug:     false,
		AutoFocus: true,
		DataPath:  dataPath,
		WindowOptions: webview2.WindowOptions{
			Title:  "Lección de Ignacio",
			Width:  1200,
			Height: 760,
			Center: true,
		},
	})
	if w == nil {
		alert("No se pudo abrir la lección.\n\nInstala Microsoft Edge WebView2 e inténtalo de nuevo.")
		return
	}
	defer w.Destroy()
	w.Navigate(url)
	w.Run()
}

func alert(text string) {
	title, _ := windows.UTF16PtrFromString("Lección de Ignacio")
	body, _ := windows.UTF16PtrFromString(text)
	_, _, _ = procMessageBox.Call(0, uintptr(unsafe.Pointer(body)), uintptr(unsafe.Pointer(title)), 0x10)
}

var procMessageBox = windows.NewLazySystemDLL("user32.dll").NewProc("MessageBoxW")
