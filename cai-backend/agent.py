import logging
from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import cartesia, openai, deepgram, silero, turn_detector
from livekit import rtc
import langid  # For language detection
import asyncio
from livekit.plugins import azure

# Load environment variables
load_dotenv(dotenv_path=".env.local")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

# Mapping for Indian languages (langid format to Azure format)
INDIAN_LANG_MAPPING = {
    "en": "en-IN",    # English (India)
    "hi": "hi-IN",    # Hindi
    "ta": "ta-IN",    # Tamil
    "te": "te-IN",    # Telugu
    "kn": "kn-IN",    # Kannada
    "ml": "ml-IN",    # Malayalam
    "mr": "mr-IN",    # Marathi
    "gu": "gu-IN",    # Gujarati
    "pa": "pa-IN",    # Punjabi
    "bn": "bn-IN",    # Bengali
    "ur": "ur-IN",    # Urdu
    "or": "or-IN",    # Odia
    "as": "as-IN",    # Assamese
}

def prewarm(proc: JobProcess):
    """Pre-load any heavy models or processes here."""
    proc.userdata["vad"] = silero.VAD.load()

def get_azure_language_code(detected_code):
    """Convert langid language code to Azure language code format for Indian languages."""
    return INDIAN_LANG_MAPPING.get(detected_code, "en-IN")  # Default to en-IN if not found

async def detect_language(text: str) -> str:
    """Detect the language of the input text using langid."""
    if not text or len(text.strip()) < 3:  # Skip detection for very short texts
        return None
        
    try:
        lang_code, confidence = langid.classify(text)
        logger.info(f"Detected language: {lang_code} (confidence: {confidence:.2f})")
        
        # Only return the language if confidence is high enough and it's supported
        if confidence > 0.5 and lang_code in INDIAN_LANG_MAPPING:
            return lang_code
        return None
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        return None

async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit voice assistant agent."""
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created for users in India. Your interface with users will be voice. "
            "You should use short and concise responses, avoiding unpronouncable punctuation. "
            "You are a multi-linguistic bot who listens to the user and responds in the same language they speak. "
            "If they speak in Hindi, respond in Hindi using proper Devanagari script, not transliterated Hinglish. "
            "Similarly for other Indian languages, always use the proper native script. "
            "If the user switches languages mid-conversation, you should respond in the new language seamlessly."
        ),
    )

    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for a participant to join the room
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

    # Default language settings for India
    default_lang_code = "en"
    default_azure_lang = "en-IN"  # English (India)

    # Create Azure STT and TTS with default language
    # Note: we're only using the parameters that are actually supported
    azure_stt = azure.STT(language=default_azure_lang)
    azure_tts = azure.TTS(language=default_azure_lang)

    # Define the voice pipeline
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=azure_stt,
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=azure_tts,
        turn_detector=turn_detector.EOUModel(),
        min_endpointing_delay=0.5,
        max_endpointing_delay=5.0,
        chat_ctx=initial_ctx,
    )

    usage_collector = metrics.UsageCollector()

    @agent.on("metrics_collected")
    def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
        """Collect and log metrics from the voice agent."""
        metrics.log_metrics(agent_metrics)
        usage_collector.collect(agent_metrics)

    # Track transcriptions for language detection
    @agent.on("transcription")
    def on_transcription(transcription):
        """Log transcriptions in the original script."""
        logger.info(f"Transcription: {transcription.text}")

    # Start the agent
    agent.start(ctx.room, participant)

    # Greet the user in Hindi and English (bilingual greeting for India)
    await agent.say("नमस्ते! Hey, how can I help you today?", allow_interruptions=True)

    # Current language tracking
    current_lang_code = default_lang_code
    
    # Main conversation loop
    while True:
        # Wait for user input
        transcription = await agent.wait_for_transcription()
        user_text = transcription.text
        
        if not user_text:
            continue

        # Detect the language of the user's input
        detected_lang = await detect_language(user_text)
        
        if detected_lang and detected_lang != current_lang_code:
            # Language has changed
            current_lang_code = detected_lang
            azure_lang_code = get_azure_language_code(detected_lang)
            
            logger.info(f"Language switched to: {detected_lang} (Azure: {azure_lang_code})")
            
            # Update the STT language - simplified to match available API
            agent.stt = azure.STT(language=azure_lang_code)
            
            # Update the TTS language
            agent.tts = azure.TTS(language=azure_lang_code)
            
            # Inform the LLM of the language change with script instructions
            script_instruction = ""
            if detected_lang == "hi":
                script_instruction = " Use Devanagari script, not transliterated Hinglish."
            elif detected_lang in ["ta", "te", "ml", "kn", "bn", "gu", "mr", "pa", "ur", "or", "as"]:
                script_instruction = " Use the proper native script for this language."
                
            agent.chat_ctx.append(
                role="system",
                text=f"The user is now speaking in {detected_lang} ({azure_lang_code}).{script_instruction} Please respond in this language.",
            )

        # Generate a response in the detected language
        response = await agent.llm.generate(
            llm.ChatContext().append(role="user", text=user_text)
        )

        # Speak the response in the current language
        await agent.say(response.text, allow_interruptions=True)

if __name__ == "__main__":
    # Run the agent using LiveKit's CLI utility
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )