package main

import (
	"log"
	"mime"
	"net/http"
	"os"
	"path/filepath"

)

var basePath string

func init() {
    basePath = os.Getenv("BASE_PATH")
    if basePath == "" {
        log.Fatal("[ERROR] BASE_PATH not set in environment")
    }
}

func serveFile(w http.ResponseWriter, r * http.Request) {

	file := r.URL.Path[len("/raw/"):]
	fullPath := filepath.Join(basePath, file)

	info, err := os.Stat(fullPath)
	if err != nil {
		if os.IsNotExist(err) {
			log.Printf("[WARN] File not found: %s\n", fullPath)
			http.NotFound(w, r)
			return
		}
		log.Printf("[ERROR] Could not access file %s: %v\n", fullPath, err)
        http.Error(w, "Internal Server Error", http.StatusInternalServerError)
        return
	}

	if info.IsDir() {
        log.Printf("[WARN] Requested path is a directory, not a file: %s\n", fullPath)
        http.NotFound(w, r)
        return
    }

	mimeType := mime.TypeByExtension(filepath.Ext(fullPath))
	if mimeType == "" {
		mimeType = "application/octet-stream" 
	}
	w.Header().Set("Content-Type", mimeType)

	http.ServeFile(w, r, fullPath)
	log.Printf("[INFO] Served file: %s (MIME: %s)\n", fullPath, mimeType)

}

func main() {

	http.HandleFunc("/raw/", serveFile)
	log.Println("Go file server running on :8000")
	log.Fatal(http.ListenAndServe(":8000", nil))
}