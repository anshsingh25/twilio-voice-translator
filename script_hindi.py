import os
import pyaudio
import wave
import threading
import queue
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-credentials.json"

# Audio playback queue to avoid overlap
audio_queue = queue.Queue()

# Translate Hindi to English
def translate_text(hindi_text):
    try:
        client = translate.Client()
        result = client.translate(hindi_text, source_language='hi', target_language='en')
        english_text = result['translatedText']
        print(f"Translated: {english_text}")
        return english_text
    except Exception as e:
        print(f"Translation error: {e}")
        return None

# Text-to-Speech (English) and save for debugging
def synthesize_and_play(english_text, file_counter):
    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=english_text)
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", name="en-US-Standard-A")
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16, sample_rate_hertz=16000)

        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

        # Save audio for debugging
        audio_file_name = f"output_audio_{file_counter}.wav"
        with open(audio_file_name, "wb") as audio_file:
            audio_file.write(response.audio_content)
            print(f"Saved audio to {audio_file_name}")

        # Add audio content to queue for playback
        audio_queue.put(response.audio_content)
    except Exception as e:
        print(f"Text-to-Speech error: {e}")

# Audio playback thread
def audio_playback_thread():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True)
    try:
        while True:
            try:
                audio_content = audio_queue.get(timeout=1)  # Wait for audio content
                print("Playing English audio...")
                stream.write(audio_content)
                audio_queue.task_done()
            except queue.Empty:
                continue
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

# Main streaming function
def main():
    if not os.path.exists("google-credentials.json"):
        print("Error: google-credentials.json not found.")
        return

    # Start audio playback thread
    playback_thread = threading.Thread(target=audio_playback_thread, daemon=True)
    playback_thread.start()

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16, sample_rate_hertz=16000, language_code="hi-IN")
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        print("Speak in Hindi (Press Ctrl+C to stop):")
    except Exception as e:
        print(f"Mic error: {e}")
        p.terminate()
        return

    file_counter = 0  # For unique audio file names
    last_processed_transcript = ""  # Track last processed transcript to avoid repeats

    def generate_requests():
        while True:
            try:
                data = stream.read(1024, exception_on_overflow=False)
                yield speech.StreamingRecognizeRequest(audio_content=data)
            except Exception as e:
                print(f"Audio read error: {e}")
                break

    requests = generate_requests()
    responses = client.streaming_recognize(streaming_config, requests)

    try:
        for response in responses:
            if not response.results or not response.results[0].alternatives:
                continue
            transcript = response.results[0].alternatives[0].transcript
            if transcript.strip() and transcript != last_processed_transcript:  # Process only new/changed transcripts
                print(f"Interim: {transcript}")
                last_processed_transcript = transcript
                english_text = translate_text(transcript)
                if english_text:
                    file_counter += 1
                    # Run synthesis in a separate thread to avoid blocking
                    threading.Thread(target=synthesize_and_play, args=(english_text, file_counter), daemon=True).start()
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Streaming error: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    main()