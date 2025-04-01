import logging
import asyncio
from typing import Optional

from dotenv import load_dotenv
from livekit import api, rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
    stt,  
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, azure, silero, turn_detector

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")

stt_plugin = None
tts_plugin = None

LANGUAGES = ["en-US", "hi-IN", "bn-IN", "pa-IN"]

class AssistantFnc(llm.FunctionContext):
    def __init__(self, *, api: api.LiveKitAPI, participant: rtc.RemoteParticipant, room: rtc.Room): 
        super().__init__()
        self.api = api
        self.participant = participant
        self.room = room
    

    @llm.ai_callable()
    async def set_language(self, detected_language: str) -> None:
        """This is a function that sets the language of the assistant.
        Call this function when you're certain the language is changed over 90%. 
        DO NOT CALL THIS FUNCTION UNDER ANY OTHER CIRCUMSTANCES. ONLY CALL THIS WHEN YOU"RE SURE THE USER HAS CHANGED THEIR LANGUAGE.
        
        Args(IMPORTANT): 
            detected_language (str): The language code of the new language. These are the supported languages.
                    "English (United States)": "en-US",
                    "Hindi (India)": "hi-IN",
                    "Bengali (India)": "bn-IN",
                    "Punjabi (India)": "pa-IN"
        
        If the user is speaking any other languages other than these four, default to english.

        Returns: None
        """
        global stt_plugin
        global tts_plugin

        print("**************************Called function set_language with language: ", detected_language)
        
        # Map language codes to appropriate voices
        voice_mapping = {
            "en-US": "en-IN-RehaanNeural",
            "hi-IN": "hi-IN-KavyaNeural",
            "bn-IN": "bn-IN-TanishaaNeural",
            "pa-IN": "pa-IN-VaaniNeural"
        }
        
        # Get the corresponding voice for the detected language
        voice = voice_mapping.get(detected_language, "en-IN-RehaanNeural")  # Default to English voice if language not found
        
        # stt_plugin.update_options(language=detected_language)
        # Update the TTS options with the new language and voice
        tts_plugin.update_options(language=detected_language, voice=voice)
        
        print(f"**************************TTS language updated to: {detected_language}, voice: {voice}")
        
        # Generate a greeting in the detected language
        greetings = {
            "en-US": "I've switched to English. How can I help you?",
            "hi-IN": "मैंने हिंदी में स्विच किया है। मैं आपकी कैसे मदद कर सकता हूँ?",
            "bn-IN": "আমি বাংলায় স্যুইচ করেছি। আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
            "pa-IN": "ਮੈਂ ਪੰਜਾਬੀ ਵਿੱਚ ਸਵਿੱਚ ਕੀਤਾ ਹੈ। ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?"
        }
        
        # Get the greeting in the detected language
        greeting = greetings.get(detected_language, greetings["en-US"])
        
        # Say the greeting in the detected language
        agent = VoicePipelineAgent.get_current()
        if agent:
            await agent.say(greeting, allow_interruptions=True)
    

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
        "- Your responses should be short, concise, and easy to understand. "
        "- Avoid using unpronounceable punctuation or complex sentences. "
    ),
)


    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")

    global stt_plugin
    global tts_plugin

    print("********************************I'm first")
    # Initialize Azure STT and TTS
    stt_plugin = azure.STT(languages=LANGUAGES)

    print("********************************", vars(stt_plugin))
    # Initialize TTS with default language and voice
    tts_plugin = azure.TTS(language="en-US", voice="en-IN-RehaanNeural")

    print(participant.metadata)



    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=stt_plugin,
        llm=openai.LLM(model="gpt-4o-mini"),  # Use a multilingual LLM
        tts=tts_plugin,
        turn_detector=turn_detector.EOUModel(),
        min_endpointing_delay=0.5,
        max_endpointing_delay=5.0,
        chat_ctx=initial_ctx,
        fnc_ctx=AssistantFnc(api=ctx.api, participant=participant, room=ctx.room),
    )

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