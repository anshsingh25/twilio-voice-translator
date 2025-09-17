import os
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate
import pyaudio
import wave

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-credentials.json"

# Step 1: Speech-to-Text (English)
def transcribe_speech():
    try:
        client = speech.SpeechClient()
        
        # Record audio (5 seconds, adjustable)
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = 1024
        RECORD_SECONDS = 5
        WAVE_OUTPUT_FILENAME = "input.wav"

        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print("Recording English speech... (Speak now)")
        frames = []
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        print("Recording complete.")
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save audio to WAV file
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        # Transcribe audio
        with open(WAVE_OUTPUT_FILENAME, 'rb') as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code="en-US"
        )

        response = client.recognize(config=config, audio=audio)
        english_text = ""
        for result in response.results:
            english_text += result.alternatives[0].transcript
        if not english_text:
            print("No speech detected.")
            return None
        print("English Text:", english_text)
        return english_text
    except Exception as e:
        print(f"Speech-to-Text error: {e}")
        return None

# Step 2: Translate English to Hindi
def translate_text(english_text):
    try:
        client = translate.Client()
        result = client.translate(english_text, source_language='en', target_language='hi')
        hindi_text = result['translatedText']
        print("Hindi Text:", hindi_text)
        return hindi_text
    except Exception as e:
        print(f"Translation error: {e}")
        return None

# Step 3: Text-to-Speech (Hindi)
def synthesize_speech(hindi_text):
    try:
        client = texttospeech.TextToSpeechClient()
        
        synthesis_input = texttospeech.SynthesisInput(text=hindi_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="hi-IN",
            name="hi-IN-Standard-A"  # Hindi female voice
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        with open("output.mp3", "wb") as out:
            out.write(response.audio_content)
        print("Hindi audio saved as output.mp3")

        # Play the audio (platform-dependent)
        if os.name == 'nt':  # Windows
            os.system("start output.mp3")
        elif os.name == 'posix':  # Linux/macOS
            os.system("mpg123 output.mp3" if os.uname().sysname == "Linux" else "afplay output.mp3")
    except Exception as e:
        print(f"Text-to-Speech error: {e}")

# Main function
def main():
    try:
        # Verify credentials file exists
        if not os.path.exists("google-credentials.json"):
            print("Error: google-credentials.json not found in the current directory.")
            return

        # Step 1: Convert speech to text
        english_text = transcribe_speech()
        if not english_text:
            return

        # Step 2: Translate to Hindi
        hindi_text = translate_text(english_text)
        if not hindi_text:
            return

        # Step 3: Convert Hindi text to speech
        synthesize_speech(hindi_text)

    except Exception as e:
        print(f"Main error: {e}")

if __name__ == "__main__":
    main()