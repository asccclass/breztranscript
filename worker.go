package main

import (
	 "os"
    "fmt"
    "os/exec"
)

func main() {
   // 先檢查 Python 是否可用
	p, err := exec.LookPath("python")
	if err != nil {
		// 嘗試 python3
		_, err = exec.LookPath("python")
		if err != nil {
			fmt.Printf("找不到 Python: %v", err)
			return
		}
		return
   }

	fileName := "ex01.wav"
	arg := fmt.Sprintf("--file_name=%s", fileName)
   cmd := exec.Command(p, "run.py", arg)

	cmd.Env = append(os.Environ(), 
      "PYTHONWARNINGS=ignore::UserWarning",
   	"TRANSFORMERS_VERBOSITY=error",
   )

   // 同時獲取標準輸出和錯誤輸出
   output, err := cmd.CombinedOutput()
    
   if err != nil {
      fmt.Printf("Command failed: %v\n", err)
   }
    
   fmt.Printf("Output: %s\n", output)
}