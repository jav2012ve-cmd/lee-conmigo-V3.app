//go:build windows

package main

import (
	"unsafe"

	"golang.org/x/sys/windows"
)

func main() {
	url := mustServer()
	if err := openBrowser(url); err != nil {
		alert("No se pudo abrir el navegador.\n\nCopia esta dirección y ábrela tú:\n" + url)
		return
	}
	alert("El libro se abrió en el navegador.\n\nDeja esta ventana abierta mientras lees.\nPulsa Aceptar solo cuando quieras cerrar el libro.")
}

func openBrowser(url string) error {
	verb, err := windows.UTF16PtrFromString("open")
	if err != nil {
		return err
	}
	target, err := windows.UTF16PtrFromString(url)
	if err != nil {
		return err
	}
	r, _, _ := procShellExecute.Call(
		0,
		uintptr(unsafe.Pointer(verb)),
		uintptr(unsafe.Pointer(target)),
		0,
		0,
		1,
	)
	if r <= 32 {
		return windows.Errno(r)
	}
	return nil
}

func alert(text string) {
	title, _ := windows.UTF16PtrFromString("Libro digital 1.7")
	body, _ := windows.UTF16PtrFromString(text)
	_, _, _ = procMessageBox.Call(0, uintptr(unsafe.Pointer(body)), uintptr(unsafe.Pointer(title)), 0x40)
}

var (
	procShellExecute = windows.NewLazySystemDLL("shell32.dll").NewProc("ShellExecuteW")
	procMessageBox   = windows.NewLazySystemDLL("user32.dll").NewProc("MessageBoxW")
)
