import spacy
import subprocess
import sys

def download_model():
    try:
        spacy.load("en_core_web_sm")
        print("Model 'en_core_web_sm' is already installed.")
    except OSError:
        print("Model 'en_core_web_sm' not found. Downloading...")
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        print("Download complete.")

if __name__ == "__main__":
    download_model()
