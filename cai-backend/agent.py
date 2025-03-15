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
from transcription_handler import handle_transcription  # Import the transcription handler
import asyncio
from livekit.plugins import azure
from livekit.plugins import google

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")


def prewarm(proc: JobProcess):
    """Pre-load any heavy models or processes here."""
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit voice assistant agent."""
    # System prompt to allow dynamic language switching
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, avoiding unpronouncable punctuation. "
            "You are a voice bot who listens to the user and responds to him in the same language he speaks. "
            "You are a multi-linguistic bot. "
            "If the user asks you to switch languages, you will respond in the requested language. "
            "Your default language is Hindi, but you can switch to any language the user requests."
        ),
    )

    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for a participant to join the room
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

    # Initialize with default language (Hindi)
    current_language = "hi-IN"

    # Define the voice pipeline
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=azure.STT(language=current_language),  # Initialize STT with default language
        llm=openai.LLM(model="gpt-4o-mini"),  # Use GPT-4 for better multilingual support
        tts=azure.TTS(language=current_language),  # Initialize TTS with default language
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

    agent.start(ctx.room, participant)

    # Agent greets the user in the default language (Hindi)
    await agent.say("नमस्ते, मैं आपकी कैसे मदद कर सकता हूँ?", allow_interruptions=True)

    # Main loop to handle dynamic language switching
    while True:
        # Wait for user input
        user_input = await agent.listen()

        # Detect the language of the user's input
        detected_language = await detect_language(user_input)

        # If the user explicitly requests a language change, update the bot's language
        if "switch to" in user_input.lower() or "change language to" in user_input.lower():
            requested_language = extract_language_from_request(user_input)
            if requested_language:
                current_language = requested_language
                agent.stt = azure.STT(language=current_language)
                agent.tts = azure.TTS(language=current_language)
                await agent.say(f"Language switched to {requested_language}.", allow_interruptions=True)
                continue

        # Respond in the detected or current language
        response = await generate_response(user_input, current_language)
        await agent.say(response, allow_interruptions=True)


async def detect_language(text: str) -> str:
    """Detect the language of the user's input using Azure STT."""
    # Use Azure STT to detect the language
    stt = azure.STT()
    result = await stt.recognize(text)
    return result.language


def extract_language_from_request(text: str) -> str:
    """Extract the requested language from the user's input."""
    # Example: "Switch to Hindi" -> "hi-IN"
    language_mapping = {
    "hindi": "hi-IN",  # Hindi
    "english": "en-US",  # English
    "tamil": "ta-IN",  # Tamil
    "telugu": "te-IN",  # Telugu
    "kannada": "kn-IN",  # Kannada
    "malayalam": "ml-IN",  # Malayalam
    "marathi": "mr-IN",  # Marathi
    "bengali": "bn-IN",  # Bengali
    "gujarati": "gu-IN",  # Gujarati
    "punjabi": "pa-IN",  # Punjabi
    "odia": "or-IN",  # Odia
    "urdu": "ur-IN",  # Urdu
    "assamese": "as-IN",  # Assamese
    "bhojpuri": "bho-IN",  # Bhojpuri (Note: Azure may not support Bhojpuri directly)
    "kashmiri": "ks-IN",  # Kashmiri
    "konkani": "kok-IN",  # Konkani
    "nepali": "ne-IN",  # Nepali
    "sanskrit": "sa-IN",  # Sanskrit
    "sindhi": "sd-IN",  # Sindhi
    "dogri": "doi-IN",  # Dogri
    "maithili": "mai-IN",  # Maithili
    "spanish": "es-ES",  # Spanish
    "french": "fr-FR",  # French
    # Add more languages as needed
}

    for lang_name, lang_code in language_mapping.items():
        if lang_name in text.lower():
            return lang_code

    return None


async def generate_response(user_input: str, language: str) -> str:
    """Generate a response in the specified language using the LLM."""
    # Use the LLM to generate a response in the requested language
    llm = openai.LLM(model="gpt-40-mini")
    response = await llm.generate(
        prompt=f"Respond to the following in {language}: {user_input}"
    )
    return response


if __name__ == "__main__":
    # Run the agent using LiveKit's CLI utility
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )