# Dental Clinic Voice Assistant

A smart, AI-powered voice assistant for dental clinics that handles patient inquiries and streamlines front-desk operations. This assistant uses natural language processing to understand patient questions and responds with a human-like voice.

## Features

- 🎙️ **Real-time speech recognition** using AssemblyAI
- 🧠 **Natural language understanding** powered by OpenAI
- 🗣️ **Realistic voice responses** using ElevenLabs voice synthesis
- 📋 **Dental domain knowledge** for handling appointment scheduling, insurance questions, and procedure information
- ⚡ **Fast response times** to provide efficient patient service

## How It Works

The assistant listens for patient voice input, transcribes it in real-time, processes the query using OpenAI's GPT model with dental context, and responds with a natural-sounding voice.

## Setup Instructions

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your API keys:

ASSEMBLYAI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here

4. Run the assistant: `python voice_bot.py`

## Use Cases

- **Patient greeting and inquiry handling**
- **Appointment scheduling information**
- **Dental insurance questions**
- **Procedure explanations and post-care instructions**
- **Emergency guidance**

## Future Enhancements

- Integration with clinic scheduling systems
- Multi-language support
- Patient record lookup capabilities
- Appointment reminder functionality
