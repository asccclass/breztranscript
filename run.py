import os
import io
import sys
import torch
import torchaudio
from transformers import WhisperProcessor, WhisperForConditionalGeneration, AutomaticSpeechRecognitionPipeline
import argparse
import warnings

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*chunk_length_s.*")
warnings.filterwarnings("ignore", message=".*return_token_timestamps.*")
# 設定輸出編碼為 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def transcribe_audio(file_name):
    # 1. Load audio
    waveform, sample_rate = torchaudio.load(file_name)          

    # 2. Preprocess
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0)                         
    waveform = waveform.squeeze().numpy()                        

    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(sample_rate, 16000)
        waveform = resampler(torch.tensor(waveform)).numpy()
        sample_rate = 16000

    # 3. Load Model
    processor = WhisperProcessor.from_pretrained("MediaTek-Research/Breeze-ASR-25")
    model = WhisperForConditionalGeneration.from_pretrained("MediaTek-Research/Breeze-ASR-25").to("cpu").eval()   #cuda

    # 4. Build Pipeline
    asr_pipeline = AutomaticSpeechRecognitionPipeline(
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        chunk_length_s=0
    )

    # 5. Inference
    output = asr_pipeline(waveform, return_timestamps=True)  
    print("Result:", output["text"])

# Set up command-line argument parsing
def parse_args():
    parser = argparse.ArgumentParser(description="Transcribe an audio file using Whisper.")
    parser.add_argument('--file_name', type=str, required=True, help="Path to the input audio file")
    return parser.parse_args()

if __name__ == "__main__":
    # Parse arguments from the command line
    args = parse_args()
    if os.name == 'nt':  # Windows
        os.system('chcp 65001')  # 設定 console 為 UTF-8
    # Call the transcription function with the provided file_name
    transcribe_audio(args.file_name)
