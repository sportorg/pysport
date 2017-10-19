package main

import (
    "os"
    "os/exec"
    "path"
    "path/filepath"
    "fmt"
    "log"
)

func main() {
    dir, err := filepath.Abs(filepath.Dir(os.Args[0]))
    if err != nil {
            log.Fatal(err)
    }
    argsWithoutProg := os.Args[1:]
    cmd := exec.Command(
        path.Join(dir, "python/pythonw.exe"),
        append([]string{path.Join(dir, "SportOrg.pyw")}, argsWithoutProg...)...)
    cmd.Stdout = os.Stdout
    cmd.Stderr = os.Stderr
    fmt.Println(cmd.Run())
}