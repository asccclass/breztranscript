package main

import(
	"os"
	"fmt"
	"strings"
	"os/exec"
)


func diagnosePythonIssue()(error) {
	fmt.Println("=== Python 環境診斷 ===")
	commands := []string{"python", "python3", "py"}  // 檢查各種 Python 命令
	
	srch := false
	result := ""
	for _, cmd := range commands {
		path, err := exec.LookPath(cmd)
		if err != nil {
			result = fmt.Sprintf("%s❌ %s: 找不到\n", result, cmd)
		} else {
			versionCmd := exec.Command(cmd, "--version")  // 嘗試獲取版本
			output, err := versionCmd.CombinedOutput()
			if err != nil {
				result = fmt.Sprintf("%s   版本檢查失敗: %v\n", result,err)
			} else {
				pythonCmd = path  // 儲存找到的 Python 命令
				pathz := strings.Replace(string(output), "\r\n", "", -1)
			   result = fmt.Sprintf("%s✅ %s: %s\n", result, pathz, path)
				srch = true
				break
			}
		}
	}
	if !srch {
		return fmt.Errorf("找不到需要的 python 環境，請先安裝 Python")		
	}
	// 檢查當前工作目錄
	pwd, _ := os.Getwd()
	result = fmt.Sprintf("%s✅ 當前工作目錄: %s\n", result, pwd)
   srch = false
	// 檢查 run.py 是否存在
	if _, err := os.Stat("run.py"); err != nil {
		result = fmt.Sprintf("%s❌ run.py 檔案不存在於當前目錄\n", result)
	} else {
		result = fmt.Sprintf("%s✅ run.py 檔案存在", result)
		srch = true
	}
	fmt.Println(result)
	if srch {
		return nil
	}
	return fmt.Errorf("Python 環境診斷未通過，請依照提示進行修正")
}