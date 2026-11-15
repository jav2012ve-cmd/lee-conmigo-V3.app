//go:build !windows

package main

import (
	"fmt"
	"os"
	"os/signal"
)

func main() {
	url := mustServer()
	fmt.Println(url)
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt)
	<-stop
}
