from pathlib import Path
from config import openai_api_key
from openai import OpenAI
import os
from pydub import AudioSegment
import importlib
import subprocess
import sys

# Initialisierung des OpenAI-Clients
client = OpenAI(api_key=openai_api_key)

# Absolute Pfade definieren
script_dir = os.path.dirname(os.path.abspath(__file__))
MP3_DIR = os.path.join(script_dir, "input")
OUTPUT_DIR = os.path.join(script_dir, "output")

# Liste der unterstützten Audio-Formate
AUDIO_FORMATS = (".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm")

# Datei aufsplitten um OpenAI Whisper-Limitierungen zu umgehen
def split_audio(file_path, chunk_length_ms=10*60*1000):
    print(f"Splitte Datei: {file_path}")
    try:
        audio = AudioSegment.from_file(file_path)
    except Exception as e:
        print(f"Fehler beim Laden der Audio-Datei {file_path}: {e}")
        print("Stellen Sie sicher, dass ffmpeg installiert ist für die Unterstützung verschiedener Audio-Formate")
        return []
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    return chunks

# Datei transkribieren
def transcribe_audio(file_path):
    print(f"Transkribiere Datei: {file_path}")
    try:
        chunks = split_audio(file_path)
        full_transcript = ""
        
        # Erstelle einen Basis-Namen für temporäre Dateien
        temp_base = os.path.join(os.path.dirname(file_path), "temp_chunk")
        
        for i, chunk in enumerate(chunks):
            # Verwende immer .mp3 als Format für temporäre Chunks
            chunk_file = f"{temp_base}_{i}.mp3"
            chunk.export(chunk_file, format="mp3")
            
            with open(chunk_file, 'rb') as audio_file:
                # Verwendung des OpenAI Clients statt direkter HTTP-Anfrage
                transcript = client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1"
                )
                full_transcript += transcript.text + " "
            
            # Optional: Temporäre Chunk-Datei löschen
            os.remove(chunk_file)
        
        # Speichere das vollständige Transkript
        transcript_file = f"{os.path.splitext(file_path)[0]}.txt"
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(full_transcript.strip())
        
        return transcript_file

    except Exception as e:
        print(f"Fehler bei der Transkription: {e}")
        return None

# Sprache des Transkripts erkennen
def detect_language(transcript):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "Du bist ein Sprachdetektions-Assistent. Antworte nur mit 'deutsch' oder 'englisch'."},
                {"role": "user", "content": f"Welche Sprache ist dieser Text?\n\n{transcript}"}
            ],
            max_tokens=5,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"Fehler bei der Spracherkennung: {e}")
        return None

# Transkript zusammenfassen
def summarize_text(transcript, language, file_name):
    try:
        system_prompt = (
            "Du bist ein Assistent für Zusammenfassungen von Transkripten (Podcasts und Videos) in deutscher Sprache. "
            "Strukturiere deine Antwort immer in folgende Abschnitte:\n"
            "1. Kernaussagen und Zusammenfassung\n"
            "2. 4-5 Hauptthemen (als Aufzählungsliste) mit jeweils 3-4 Sätze Erläuterungen\n"
            "3. Erwähnte Methoden (als Aufzählungsliste, diesen Abschnitt nur einschließen wenn Methoden erwähnt wurden)\n"
            "4. Wichtige Personen und Unternehmen (als Aufzählungsliste, diesen Abschnitt nur einschließen wenn relevant)\n"
            "5. Lektionen für Produktmanager, Businesss Designer und UX-Strategen (als Aufzählungsliste, diesen Abschnitt nur einschließen wenn relevant)\n"
        )
        
        if language == "deutsch":
            user_prompt = (
                f"Analysiere das folgende Transkript und erstelle eine strukturierte Zusammenfassung. "
                f"Arbeite die wichtigsten Punkte klar heraus.\n\n{transcript}"
            )
        else:
            user_prompt = (
                f"Analysiere das folgende englische Transkript und erstelle eine strukturierte Zusammenfassung auf Deutsch. "
                f"Arbeite die wichtigsten Punkte klar heraus.\n\n{transcript}"
            )

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
        )
        summary = response.choices[0].message.content.strip()

        markdown = (
            f"# Zusammenfassung des Transcript: {file_name}\n\n"
            f"## Zusammenfassung\n\n{summary}\n\n"
            f"## Original-Transkript\n\n{transcript}"
        )

        return markdown

    except Exception as e:
        print(f"Fehler beim Zusammenfassen: {e}")
        return None

def process_podcasts():
    for file in os.listdir(MP3_DIR):
        if file.endswith(AUDIO_FORMATS + (".txt",)):
            base_name = os.path.splitext(file)[0]
            file_path = os.path.join(MP3_DIR, file)
            expected_transcript_file = f"{os.path.splitext(file_path)[0]}.txt"
            expected_summary_file = os.path.join(OUTPUT_DIR, f"{base_name}_summary.md")
            
            # Prüfe ob Zusammenfassung bereits existiert
            if os.path.exists(expected_summary_file):
                print(f"Zusammenfassung für {file} existiert bereits, überspringe Verarbeitung.")
                continue
            
            # Hole Transkript (entweder aus txt oder durch Transkription)
            if file.endswith(".txt"): # Text-Datei
                transcript_file = file_path
            else: # Audio-Datei
                if os.path.exists(expected_transcript_file):
                    print(f"Transkript für {file} existiert bereits, überspringe Transkription.")
                    transcript_file = expected_transcript_file
                else:
                    transcript_file = transcribe_audio(file_path)
            
            if transcript_file and os.path.exists(transcript_file):
                with open(transcript_file, "r", encoding="utf-8") as f:
                    transcript = f.read()
                
                # Überprüfen, ob das Transkript eine Mindestlänge hat
                if len(transcript) < 500:
                    print(f"Transkript für {file} scheint unvollständig zu sein.")
                    continue
                
                # Sprache prüfen
                language = detect_language(transcript)
                if not language:
                    print(f"Konnte Sprache für {file} nicht erkennen, verwende Deutsch als Standard")
                    language = "deutsch"
                
                markdown = summarize_text(transcript, language, file)
                if markdown:
                    with open(expected_summary_file, "w", encoding="utf-8") as f:
                        f.write(markdown)
                    print(f"Zusammenfassung gespeichert: {expected_summary_file}")

def check_requirements():
    """Überprüft, ob alle notwendigen Voraussetzungen erfüllt sind."""
    
    # Prüfe benötigte Python-Pakete
    required_packages = ['openai', 'pydub']
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Fehlende Python-Pakete gefunden:")
        print(f"Bitte installiere sie mit: pip install {' '.join(missing_packages)}")
        sys.exit(1)
    
    # Prüfe config.py und API Key
    try:
        from config import openai_api_key
        if not openai_api_key or openai_api_key == "Dein-API-Key-hier":
            print("❌ Ungültiger API Key in config.py")
            print("Bitte trage deinen OpenAI API Key in der config.py ein")
            sys.exit(1)
    except ImportError:
        print("❌ config.py nicht gefunden")
        print("Bitte erstelle eine config.py mit deinem OpenAI API Key:")
        print('openai_api_key = "Dein-API-Key-hier"')
        sys.exit(1)
    
    # Prüfe FFmpeg Installation
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg ist nicht installiert")
        print("Bitte installiere FFmpeg:")
        print("Windows: winget install FFmpeg")
        print("macOS: brew install ffmpeg")
        print("Linux: sudo apt install ffmpeg")
        sys.exit(1)
    
    # Prüfe Verzeichnisstruktur
    for dir_name in ["input", "output"]:
        dir_path = os.path.join(script_dir, dir_name)
        if not os.path.exists(dir_path):
            print(f"✨ Erstelle {dir_name} Verzeichnis")
            os.makedirs(dir_path)
    
    print("✅ Alle Voraussetzungen sind erfüllt!")

# Füge dies am Anfang der process_transcripts() Funktion ein
if __name__ == "__main__":
    check_requirements()
    process_podcasts()
