import logging
import asyncio
from typing import Optional

from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
    stt,  # Import stt module for SpeechEvent
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, azure, silero, turn_detector

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
    role="system",
    text=(
        "You are a multilingual voice assistant. "
        "IMPORTANT: "
        "- You will carefully detect the language the user is speaking in and respond in the same language. "
        "- If the user switches their language mid-conversation, you must immediately switch to the user's new language and respond in that language. "
        "- Always assess the user's language carefully and ensure your responses are in the correct language. "
        "- If the user speaks in Hinglish (a blend of Hindi and English), you should also respond in Hinglish to maintain a smoother, more natural conversation. "
        "- Your responses should be short, concise, and easy to understand. "
        "- Avoid using unpronounceable punctuation or complex sentences. "
    ),
)


    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

    # Initialize Azure STT and TTS
    stt_plugin = azure.STT(languages=["en-US", "hi-IN", "ta-IN", "kn-IN"])
    tts_plugin = azure.TTS()

    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=stt_plugin,
        llm=openai.LLM(model="gpt-4o-mini"),  # Use a multilingual LLM
        tts=tts_plugin,
        turn_detector=turn_detector.EOUModel(),
        min_endpointing_delay=0.5,
        max_endpointing_delay=5.0,
        chat_ctx=initial_ctx,
    )

    usage_collector = metrics.UsageCollector()

    @agent.on("metrics_collected")
    def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
        metrics.log_metrics(agent_metrics)
        usage_collector.collect(agent_metrics)

    # Track the current language
    current_language = "en-US"  # Default language

    @agent.on("user_speech_committed")
    def on_user_speech_committed(event: stt.SpeechEvent):
        logger.info("***************************user_speech_committed event received")  # Log when the event is received
        # logger.info(f"Event type: {type(event)}")  # Log the type of the event object
        # Use asyncio.create_task to handle async operations
        asyncio.create_task(_handle_user_speech_committed(event))

    async def _handle_user_speech_committed(event: stt.SpeechEvent):
        nonlocal current_language

        # Log the event object and its properties
        logger.info(f"Event details: {event}")
        logger.info(f"Event type: {event.type}")
        logger.info(f"Event alternatives: {event.alternatives}")

        # Get the detected language from the STT event
        if event.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
            detected_language = event.alternatives[0].language
            logger.info(f"*************************Detected language: {detected_language}")  # Log the detected language
            if detected_language and detected_language != current_language:
                logger.info(f"************************Detected language change: {current_language} -> {detected_language}")
                current_language = detected_language

                # Update STT and TTS languages dynamically
                stt_plugin.update_options(languages=[detected_language])
                tts_plugin.update_options(language=detected_language)

                # Notify the user of the language switch
                await agent.say(f"Switching to {detected_language}.", allow_interruptions=False)

    agent.start(ctx.room, participant)

    # The agent should be polite and greet the user when it joins :)
    await agent.say("Hey, how can I help you today?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )