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
	url := mustServer()
	dataPath := filepath.Join(os.TempDir(), "LeeConmigoLibro")
	w := webview2.NewWithOptions(webview2.WebViewOptions{
		Debug:     false,
		AutoFocus: true,
		DataPath:  dataPath,
		WindowOptions: webview2.WindowOptions{
			Title:  "Libro digital 1.6",
			Width:  1200,
			Height: 760,
			Center: true,
		},
	})
	if w == nil {
		alert("No se pudo abrir el libro.\n\nInstala Microsoft Edge WebView2 e inténtalo de nuevo.")
		return
	}
	defer w.Destroy()
	w.Navigate(url)
	w.Run()
}

func alert(text string) {
	title, _ := windows.UTF16PtrFromString("Libro digital 1.6")
	body, _ := windows.UTF16PtrFromString(text)
	_, _, _ = procMessageBox.Call(0, uintptr(unsafe.Pointer(body)), uintptr(unsafe.Pointer(title)), 0x10)
}

var procMessageBox = windows.NewLazySystemDLL("user32.dll").NewProc("MessageBoxW")
