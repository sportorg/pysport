package main

import (
    "os"
    "os/exec"
    "path"
    "path/filepath"
    "log"
)

func getGlobalPython() string {
	return "pythonw"
}

func baseDir(p string) string {
	dir, err := filepath.Abs(filepath.Dir(os.Args[0]))
    if err != nil {
		log.Fatal(err)
    }
    return path.Join(dir, p)
}

func hasPython(p string) bool {
	cmd := exec.Command(p)
	if cmd.Run() == nil {
		return true
	}
	return false
}

func main() {
    argsWithoutProg := os.Args[1:]

    var pythonName = getGlobalPython()

	cmd := exec.Command(
        pythonName,
        append([]string{baseDir("SportOrg.pyw")}, argsWithoutProg...)...)

    cmd.Stdout = os.Stdout
    cmd.Stderr = os.Stderr
    log.Println(cmd.Run())
}