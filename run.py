import os
import io
import sys
import tempfile
from unittest import result
import torch
import torchaudio
import numpy as np
from transformers import WhisperProcessor, WhisperForConditionalGeneration, AutomaticSpeechRecognitionPipeline
import argparse
import warnings

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*chunk_length_s.*")
warnings.filterwarnings("ignore", message=".*return_token_timestamps.*")
# 設定輸出編碼為 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


"""
   載入 Breeze ASR 25 模型並回傳模型物件和錯誤資訊。
   若成功，回傳 (asr_pipeline, None)。
   若失敗，回傳 (None, 錯誤訊息)。
"""
def load_model(name):
    global processor, model, asr_pipeline
    try:
        processor = WhisperProcessor.from_pretrained(name)
        model = WhisperForConditionalGeneration.from_pretrained(name)

        # 檢查是否有 CUDA
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device).eval()
        
        # 建立 pipeline
        asr_pipeline = AutomaticSpeechRecognitionPipeline(
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            chunk_length_s=0,
            device=device
        )
        return asr_pipeline, None
    except Exception as e:
        return None, f"❌ 模型載入失敗: {str(e)}"

def transcribe_audio(file_name):
    if file_name is None:
        print("❌ 請提供有效的音訊檔案路徑")
        return
    if isinstance(file_name, str):
        audio_path = file_name
    elif isinstance(file_name, tuple):
        sample_rate, audio_data = file_name
        # 建立臨時檔案
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:  # 確保音訊數據格式正確        
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            if audio_data.max() > 1.0:  # 正規化音訊
                audio_data = audio_data / 32768.0
            torchaudio.save(tmp_file.name, torch.tensor(audio_data).unsqueeze(0), sample_rate)  # 儲存為 wav 檔案
            audio_path = tmp_file.name
    else:
       return "❌ 不支援的音訊格式", "", "", ""


    waveform, sample_rate = torchaudio.load(audio_path)   # 1. Load audio 預處理音訊
    if waveform.shape[0] > 1:  # 2. Preprocess 轉為單聲道
        waveform = waveform.mean(dim=0)                         
    waveform = waveform.squeeze().numpy()                        
    if sample_rate != 16000:  # 重採樣到 16kHz
        resampler = torchaudio.transforms.Resample(sample_rate, 16000)
        waveform = resampler(torch.tensor(waveform)).numpy()
        sample_rate = 16000
    # 3. Load Model、# 4. Build Pipeline
    asr_pipeline, error = load_model("MediaTek-Research/Breeze-ASR-25")
    if error:
        print(error)
        return
    result = asr_pipeline(waveform, return_timestamps=True)   # 5. Inference
    if isinstance(file_name, tuple) and os.path.exists(audio_path):  # 清理臨時檔案
        os.unlink(audio_path)
    transcription = result["text"].strip() # 格式化結果

    # 格式化時間戳記顯示
    #formatted_text = ""
    pure_text = ""
    srt_text = ""

    if "chunks" in result and result["chunks"]:
        for i, chunk in enumerate(result["chunks"], 1):
            start_time = chunk["timestamp"][0] if chunk["timestamp"][0] is not None else 0
            end_time = chunk["timestamp"][1] if chunk["timestamp"][1] is not None else 0
            text = chunk['text'].strip()
            
            if text:  # 只處理非空文字
                # 格式化顯示文字
                #formatted_text += f"[{start_time:.2f}s - {end_time:.2f}s]: {text}\n"
                
                # 純文字（不含時間戳記）
                pure_text += f"{text}\n"
                
                # SRT 格式
                start_srt = f"{int(start_time//3600):02d}:{int((start_time%3600)//60):02d}:{int(start_time%60):02d},{int((start_time%1)*1000):03d}"
                end_srt = f"{int(end_time//3600):02d}:{int((end_time%3600)//60):02d}:{int(end_time%60):02d},{int((end_time%1)*1000):03d}"
                srt_text += f"{i}\n{start_srt} --> {end_srt}\n{text}\n\n"
    else:
        # 如果沒有時間戳記，只顯示文字
        # formatted_text = transcription
        pure_text = transcription
        srt_text = f"1\n00:00:00,000 --> 00:00:10,000\n{transcription}\n\n"

    print("Result:\n", pure_text.strip(), srt_text.strip())

# Set up command-line argument parsing
def parse_args():
    parser = argparse.ArgumentParser(description="Transcribe an audio file using Whisper.")
    parser.add_argument('--file_name', type=str, required=True, help="Path to the input audio file")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()  # Parse arguments from the command line
    if os.name == 'nt':  # Windows
        os.system('chcp 65001')  # 設定 console 為 UTF-8
    transcribe_audio(args.file_name)  # Call the transcription function with the provided file_name
