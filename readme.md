# Transcript Summary Generator

Dieses Skript konvertiert Audio-Dateien in Text und erstellt daraus strukturierte Zusammenfassungen mithilfe von OpenAI's Whisper und GPT-4.

## Voraussetzungen

### 1. Python-Installation
- Python 3.8 oder höher
- pip (Python Package Manager)

### 2. FFmpeg Installation
FFmpeg wird für die Audio-Verarbeitung benötigt:

**Windows:**
```bash
winget install FFmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 3. Python-Pakete
Installiere die benötigten Python-Pakete:
```bash
pip install openai pydub
```

### 4. OpenAI API-Key
1. Erstelle einen Account bei [OpenAI](https://platform.openai.com)
2. Generiere einen API-Key
3. Erstelle eine `config.py` Datei im gleichen Verzeichnis mit folgendem Inhalt:
```python
openai_api_key = "Dein-API-Key-hier"
```

## Verzeichnisstruktur
```
.
├── transcript-summary.py
├── config.py
├── input/
│   └── [Deine Audio-Dateien hier]
└── output/
    └── [Generierte Zusammenfassungen erscheinen hier]
```

## Verwendung

1. Lege deine Audio-Dateien im `input`-Verzeichnis ab
2. Führe das Skript aus:
```bash
python transcript-summary.py
```

Beim ersten Start prüft das Skript automatisch:
- ✅ Ob alle benötigten Python-Pakete installiert sind
- ✅ Ob die config.py mit einem gültigen API-Key existiert
- ✅ Ob FFmpeg korrekt installiert ist
- ✅ Ob die benötigten Verzeichnisse existieren (werden ggf. automatisch erstellt)

Falls etwas fehlt, erhältst du eine entsprechende Meldung mit Installationsanweisungen.

Nach erfolgreicher Prüfung wird das Skript:
- Audio-Dateien in Text transkribieren
- Eine strukturierte Zusammenfassung erstellen
- Die Ergebnisse im `output`-Verzeichnis als Markdown-Dateien speichern

## Output-Format
Die generierten Zusammenfassungen enthalten:
1. Kernaussagen und Zusammenfassung
2. 4-5 Hauptthemen mit Erläuterungen
3. Erwähnte Methoden (falls vorhanden)
4. Wichtige Personen und Unternehmen (falls relevant)
5. Lektionen für Produktmanager, Business Designer und UX-Strategen (falls relevant)

## Hinweise
- Das Skript verarbeitet Audio-Dateien in Chunks von 10 Minuten
- Bereits verarbeitete Dateien werden übersprungen
- Du kannst auch direkt Transkript-Dateien (.txt) im input-Verzeichnis ablegen
- Die Zusammenfassungen werden auf Deutsch erstellt, auch wenn das Original in Englisch ist

## Fehlerbehebung
Falls Fehler auftreten:
1. Führe das Skript erneut aus - die automatischen Checks zeigen dir, was fehlt
2. Stelle sicher, dass FFmpeg korrekt installiert ist
3. Überprüfe deinen OpenAI API-Key
4. Stelle sicher, dass die Audio-Dateien nicht beschädigt sind
5. Prüfe, ob genügend Speicherplatz verfügbar ist