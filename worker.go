package main

import (
	 "os"
    "fmt"
    "os/exec"
)

var (
	pythonCmd   string
	dirPath		string
)
// 輔助函數：檢查是否為已知警告
func isKnownWarning(output string) bool {
	knownWarnings := []string{
		"torchaudio._backend.utils.py",
		"chunk_length_s` is very experimental",
		"return_token_timestamps` is deprecated",
		"Using custom `forced_decoder_ids`",
		"Transcription using a multilingual Whisper",
		"UserWarning:",
	}
	
	for _, warning := range knownWarnings {
		if fmt.Sprintf("%s", output) != "" && len(output) > 10 {
			// 簡單的包含檢查
			for _, char := range warning {
				found := false
				for _, outChar := range output {
					if char == outChar {
						found = true
						break
					}
				}
				if !found {
					return false
				}
			}
			return true
		}
	}
	return false
}

func main() {
	if err := diagnosePythonIssue(); err != nil {
		fmt.Println(err.Error())
		return
	}

	fileName := "ex01.wav"
	arg := fmt.Sprintf("--file_name=%s", fileName)
	cmd := exec.Command(pythonCmd, "run.py", arg)
	cmd.Env = append(os.Environ(),                  // 設定環境變數
		"PYTHONWARNINGS=ignore::UserWarning",
		"TRANSFORMERS_VERBOSITY=error",
	)
	// 分別處理 stdout 和 stderr
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		fmt.Printf("Command failed: %v\n", err)
		return
	}
	stderr, err := cmd.StderrPipe()
	if err != nil {
		fmt.Printf("Command failed: %v\n", err)
		return
	}
	if err := cmd.Start(); err != nil {
		fmt.Printf("Command failed: %v\n", err)
		return
	}
	// 讀取並過濾輸出
	go func() {
		buf := make([]byte, 1024)
		for {
			n, err := stdout.Read(buf)
			if n > 0 {
				fmt.Print(string(buf[:n]))
			}
			if err != nil {
				break
			}
		}
	}()

	go func() {
		buf := make([]byte, 1024)
		for {
			n, err := stderr.Read(buf)
			if n > 0 {
				output := string(buf[:n])
				// 過濾掉已知的警告
				if !isKnownWarning(output) {
					fmt.Print("【警告/錯誤】", output)
				}
			}
			if err != nil {
				break
			}
		}
	}()
	if err := cmd.Wait(); err != nil {
		fmt.Printf("Command failed: %v\n", err)
		return
	}
	return
}