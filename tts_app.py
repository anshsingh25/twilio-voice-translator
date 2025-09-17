import os
import pyaudio
import wave
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-credentials.json"

# Step 1: Speech-to-Text (English)
def transcribe_speech():
    try:
        client = speech.SpeechClient()
        
        # Record audio for 5 seconds (adjustable)
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = 1024
        RECORD_SECONDS = 5
        WAVE_OUTPUT_FILENAME = "input.wav"

        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print(f"Recording English speech for {RECORD_SECONDS} seconds...")
        frames = []
        
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        
        print("Recording complete.")
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save audio to temporary WAV file
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
        
        # Clean up temporary WAV file
        os.remove(WAVE_OUTPUT_FILENAME)
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

# Step 3: Text-to-Speech (Hindi) - Play directly without saving
def synthesize_speech(hindi_text):
    try:
        client = texttospeech.TextToSpeechClient()
        
        synthesis_input = texttospeech.SynthesisInput(text=hindi_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="hi-IN",
            name="hi-IN-Standard-A"  # Hindi female voice
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,  # Raw PCM for direct playback
            sample_rate_hertz=16000
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Play audio directly using PyAudio
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        output=True)
        print("Playing Hindi speech...")
        stream.write(response.audio_content)
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Hindi speech played.")
    except Exception as e:
        print(f"Text-to-Speech error: {e}")

# Main function
def main():
    try:
        # Verify credentials file
        if not os.path.exists("google-credentials.json"):
            print("Error: google-credentials.json not found in the current directory.")
            return False

        # Step 1: Convert speech to text
        english_text = transcribe_speech()
        if not english_text:
            return True  # Continue loop even if no speech detected

        # Step 2: Translate to Hindi
        hindi_text = translate_text(english_text)
        if not hindi_text:
            return True  # Continue loop on translation error

        # Step 3: Convert Hindi text to speech and play directly
        synthesize_speech(hindi_text)
        return True

    except Exception as e:
        print(f"Main error: {e}")
        return True  # Continue loop on general error

# Run continuously until aborted
if __name__ == "__main__":
    print("Starting program. Press Ctrl+C to abort.")
    try:
        while True:
            if not main():
                break  # Exit if credentials file is missing
            print("\nReady for next recording. Press Ctrl+C to stop.")
    except KeyboardInterrupt:
        print("\nProgram aborted by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")