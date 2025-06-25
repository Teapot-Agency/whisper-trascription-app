# 🎙️ Whisper Transcription App

A modern web application for audio transcription using OpenAI's Whisper v3 model, built with Streamlit.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-red.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-Whisper%20v3-green.svg)

## ✨ Features

- 🎵 **Audio Transcription** - Support for MP3, WAV, M4A, and more audio formats
- 🌍 **Multi-language Support** - Auto-detect or specify language
- 📝 **Custom Naming** - Name your transcriptions for easy reference
- 🔍 **Search History** - Search through transcription names and content
- 💾 **Export Options** - Download individual transcriptions or export full history
- 🎨 **Modern UI** - Clean, Tailwind-inspired interface
- 🔐 **Secure** - API keys stored in environment variables

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/whisper-transcription-app.git
   cd whisper-transcription-app
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Run the app:**
   ```bash
   streamlit run transcription_app.py
   ```

5. **Open in browser:**
   Navigate to `http://localhost:8501`

## 🌐 Deploy Online

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions on deploying to:
- Streamlit Community Cloud (FREE)
- Heroku
- Railway
- Render
- Google Cloud Run

## 📖 Usage

1. **Enter API Key** - Add your OpenAI API key (stored securely)
2. **Upload Audio** - Select an audio file from your computer
3. **Configure Options** - Set custom name and language (optional)
4. **Transcribe** - Click the transcribe button
5. **View & Export** - View results and download transcriptions

## 💰 Costs

- **OpenAI Whisper API:** $0.006 per minute of audio
- **Example:** 1 hour of audio = $0.36

## 🔒 Security

- API keys are stored in environment variables
- Never commit `.env` files to version control
- Consider adding authentication for production deployments

## 📁 Project Structure

```
whisper-transcription-app/
├── transcription_app.py    # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment variables
├── .gitignore            # Git ignore file
├── README.md             # This file
└── DEPLOYMENT_GUIDE.md   # Deployment instructions
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- OpenAI for the amazing Whisper API
- Streamlit for the wonderful web framework
- The open-source community

---

Made with ❤️ using Streamlit and OpenAI Whisper