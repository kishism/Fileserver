package envLoader

import (
	"bufio"
	"log"
	"os"
	"strings"
)

func Load(filename string) error {
	file, err := os.Open(filename)
	if err != nil {
		return err
	}

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())

		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
            log.Printf("[WARN] Invalid line in %s: %s\n", filename, line)
            continue
        }

		key := strings.TrimSpace(parts[0])
		value := strings.TrimSpace(parts[1])

		value = strings.Trim(value, "\"'")

		os.Setenv(key, value)
	}

	if err := scanner.Err(); err != nil {
		return err
	}

	return nil
}