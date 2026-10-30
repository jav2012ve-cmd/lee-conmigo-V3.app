//go:build !windows

package main

import (
	"fmt"
	"os"
	"os/signal"
)

func main() {
	fmt.Println(startServer())
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt)
	<-stop
}
