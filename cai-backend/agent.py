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
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, avoiding unpronouncable punctuation."
            "You are a voice bot who listens to the user and responds to him in the same language he speaks"
            "You are a multi-linguistic bot"
        ),
    )

    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for a participant to join the room
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

    # Define the voice pipeline
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        # stt=deepgram.STT(model="nova-2-general"),
        stt=azure.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=azure.TTS(),
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

    # Agent greets the user
    await agent.say("Hey, how can I help you today?", allow_interruptions=True)


if __name__ == "__main__":
    # Run the agent using LiveKit's CLI utility
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
