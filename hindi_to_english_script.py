import os
import pyaudio
import wave
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-credentials.json"

# Step 1: Speech-to-Text (Hindi)
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
        print(f"Recording Hindi speech for {RECORD_SECONDS} seconds...")
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
            language_code="hi-IN"  # Changed to Hindi
        )

        response = client.recognize(config=config, audio=audio)
        hindi_text = ""
        for result in response.results:
            hindi_text += result.alternatives[0].transcript
        if not hindi_text:
            print("No speech detected.")
            return None
        print("Hindi Text:", hindi_text)
        
        # Clean up temporary WAV file
        os.remove(WAVE_OUTPUT_FILENAME)
        return hindi_text
    except Exception as e:
        print(f"Speech-to-Text error: {e}")
        return None

# Step 2: Translate Hindi to English
def translate_text(hindi_text):
    try:
        client = translate.Client()
        result = client.translate(hindi_text, source_language='hi', target_language='en')  # Reversed languages
        english_text = result['translatedText']
        print("English Text:", english_text)
        return english_text
    except Exception as e:
        print(f"Translation error: {e}")
        return None

# Step 3: Text-to-Speech (English) - Play directly without saving
def synthesize_speech(english_text):
    try:
        client = texttospeech.TextToSpeechClient()
        
        synthesis_input = texttospeech.SynthesisInput(text=english_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",  # Changed to English
            name="en-US-Standard-C"  # English female voice
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
        print("Playing English speech...")
        stream.write(response.audio_content)
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("English speech played.")
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
        hindi_text = transcribe_speech()
        if not hindi_text:
            return True  # Continue loop even if no speech detected

        # Step 2: Translate to English
        english_text = translate_text(hindi_text)
        if not english_text:
            return True  # Continue loop on translation error

        # Step 3: Convert English text to speech and play directly
        synthesize_speech(english_text)
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