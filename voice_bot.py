import assemblyai as aai
import time
import threading
import queue
import pyaudio
import wave
import os
import requests
from openai import OpenAI
import json
import tempfile
import pygame
import sys  # Add this for system exit
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DentalClinicAssistant:
    def __init__(self):
        # Hardcode API keys directly to avoid environment variable issues
        self.assemblyai_api_key = "Assembly-API"
        self.openai_api_key = "Openai-API"
        self.elevenlabs_api_key = "Elevenlabs-API"
        
        # Print API keys for debugging (first few chars only)
        print(f"AssemblyAI API key: {self.assemblyai_api_key[:5]}...")
        print(f"ElevenLabs API key: {self.elevenlabs_api_key[:5]}...")
        
        # Configure AssemblyAI - this line is crucial
        aai.settings.api_key = self.assemblyai_api_key
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Initialize conversation context
        self.conversation_history = [
            {"role": "system", "content": "You are Sandy, a professional and friendly receptionist at Vancouver Dental Clinic. Your responses should be helpful, concise, and focused on dental clinic services. You can provide information about dental procedures, appointment scheduling, insurance questions, and general dental health advice. If you don't know something specific, offer to take a message or suggest when a dentist will be available to answer. Keep your responses relatively brief (1-3 sentences if possible) as they will be spoken out loud."}
        ]
        
        # Initialize audio components
        self.audio_queue = queue.Queue()
        self.transcriber = None
        self.recording = False
        self.audio_thread = None
        pygame.mixer.init()
        
        # For recording
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        self.audio = pyaudio.PyAudio()
        
        # Initialize state variables
        self.is_listening = False
        self.temp_audio_file = None
        
    def start(self):
        """Start the assistant with a greeting"""
        print("\n=== Dental Clinic Voice Assistant ===\n")
        greeting = "Thank you for calling Vancouver Dental Clinic. My name is Sandy, how may I assist you today?"
        print(f"Assistant: {greeting}")
        self.generate_and_play_audio(greeting)
        
        # Start the voice recognition process
        self.start_listening()
        
        try:
            while True:
                time.sleep(0.1)  # Just to prevent high CPU usage in the main thread
        except KeyboardInterrupt:
            print("\nShutting down assistant...")
            self.stop_listening()
            print("Assistant stopped. Thank you for using the Dental Clinic Voice Assistant!")
    
    def start_listening(self):
        """Start listening for user speech"""
        if self.is_listening:
            return
            
        self.is_listening = True
        print("\nListening...")
        
        # Configure the real-time transcriber
        self.transcriber = aai.RealtimeTranscriber(
            sample_rate=self.RATE,
            on_data=self.on_transcript_data,
            on_error=self.on_transcript_error,
            on_open=self.on_connection_open,
            on_close=self.on_connection_close,
            end_utterance_silence_threshold=1000  # 1 second of silence to end an utterance
        )
        
        # Start microphone input thread
        self.recording = True
        self.audio_thread = threading.Thread(target=self.record_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        
        # Connect to AssemblyAI
        self.transcriber.connect()
    
    def stop_listening(self):
        """Stop listening for user speech"""
        if not self.is_listening:
            return
            
        self.is_listening = False
        self.recording = False
        
        if self.transcriber:
            self.transcriber.close()
            self.transcriber = None
            
        if self.audio_thread:
            self.audio_thread.join(timeout=1)
    
    def record_audio(self):
        """Record audio from microphone and send to transcriber"""
        stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        try:
            while self.recording:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                # Fixed the is_connected issue
                if self.transcriber:
                    self.transcriber.stream(data)
        finally:
            stream.stop_stream()
            stream.close()
    
    def on_connection_open(self, session_opened):
        """Callback when AssemblyAI connection is opened"""
        # Connection is open but no need to print a message
        pass
    
    def on_transcript_data(self, transcript):
        """Process transcript data from AssemblyAI"""
        if not transcript.text:
            return
            
        if isinstance(transcript, aai.RealtimeFinalTranscript):
            user_text = transcript.text.strip().lower()
            print(f"\nPatient: {transcript.text}")
            
            # Check for goodbye phrases immediately
            goodbye_phrases = ["bye", "goodbye", "exit", "quit", "end call", "thank you bye", "thanks bye"]
            
            # More direct check for single word "bye"
            if user_text == "bye" or user_text == "by" or user_text == "goodbye":
                self.handle_goodbye()
            # Check for other goodbye phrases
            elif any(phrase in user_text for phrase in goodbye_phrases):
                self.handle_goodbye()
            else:
                self.process_user_input(transcript.text)
    
    def handle_goodbye(self):
        """Handle goodbye phrase and exit the program"""
        # Stop listening
        self.stop_listening()
        
        # Generate a goodbye response
        goodbye_message = "Thank you for calling Vancouver Dental Clinic. Goodbye and have a great day!"
        print(f"Assistant: {goodbye_message}")
        
        # Generate and play the goodbye audio
        self.generate_and_play_audio(goodbye_message)
        
        # Give time for the goodbye message to be spoken (important!)
        time.sleep(5)
        
        print("\n=== Call Ended ===")
        
        # Exit the program safely
        sys.exit(0)
    
    def on_transcript_error(self, error):
        """Handle transcription errors"""
        # Only print critical errors
        if "paid-only" not in str(error):
            print(f"Error: {error}")
    
    def on_connection_close(self):
        """Handle connection close"""
        # Connection is closed but no need to print a message
        pass
    
    def process_user_input(self, text):
        """Process user input and generate AI response"""
        # Temporarily stop listening while processing
        self.stop_listening()
        
        # Add user input to conversation history
        self.conversation_history.append({"role": "user", "content": text})
        
        try:
            # Get response from OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history,
                max_tokens=150  # Limiting token count for concise responses
            )
            
            # Extract and store the assistant's response
            assistant_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            
            # Display the response
            print(f"Assistant: {assistant_response}")
            
            # Generate and play audio response
            self.generate_and_play_audio(assistant_response)
            
        except Exception as e:
            print(f"Error generating response: {e}")
            fallback_response = "I'm sorry, I'm having trouble processing that request. Could you please repeat that?"
            print(f"Assistant: {fallback_response}")
            self.generate_and_play_audio(fallback_response)
        
        # Resume listening
        self.start_listening()
    
    def generate_and_play_audio(self, text):
        """Generate and play audio using ElevenLabs API"""
        try:
            # ElevenLabs API endpoint
            url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"  # Rachel voice ID
            
            # Request headers - make sure xi-api-key is set correctly
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key  # This line is crucial
            }
            
            # Request body
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.7,  # Increased for clearer speech
                    "similarity_boost": 0.5
                }
            }
            
            # Make the API request
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # Create a temporary file to store the audio with a unique name
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False, prefix='voice_') as temp_file:
                    temp_file.write(response.content)
                    self.temp_audio_file = temp_file.name
                
                # Play the audio using pygame
                pygame.mixer.music.load(self.temp_audio_file)
                pygame.mixer.music.play()
                
                # Wait for the audio to finish playing
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                # Clean up the temporary file
                try:
                    if self.temp_audio_file and os.path.exists(self.temp_audio_file):
                        os.unlink(self.temp_audio_file)
                        self.temp_audio_file = None
                except:
                    # Ignore errors during cleanup
                    pass
            else:
                print(f"Error: Could not generate speech")
        
        except Exception as e:
            print(f"Error: Speech generation failed")

if __name__ == "__main__":
    assistant = DentalClinicAssistant()
    assistant.start()