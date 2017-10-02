package main

import (
    "log"
    "os"
    "os/exec"
)

func main() {
    cmd := exec.Command("python/pythonw.exe", "SportOrg.pyw")
    cmd.Stdout = os.Stdout
    cmd.Stderr = os.Stderr
    log.Println(cmd.Run())
}