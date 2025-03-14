# transcription_handler.py
import asyncio
from livekit.agents import stt, transcription
from livekit.plugins.deepgram import STT
from livekit import rtc

async def _forward_transcription(
    stt_stream: stt.SpeechStream,
    stt_forwarder: transcription.STTSegmentsForwarder,
):
    """Forward transcription segments and log the transcript in the console."""
    async for ev in stt_stream:
        stt_forwarder.update(ev)

        # Print or log transcriptions
        if ev.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
            print(ev.alternatives[0].text, end="")
        elif ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
            print("\n -> ", ev.alternatives[0].text)


async def handle_transcription(job, participant: rtc.RemoteParticipant, track: rtc.Track):
    """Handles transcription setup for a participant's audio track."""
    stt_service = STT(model="nova-2-general")  # Configure the STT model
    audio_stream = rtc.AudioStream(track)

    # Set up transcription forwarding to frontend
    stt_forwarder = transcription.STTSegmentsForwarder(
        room=job.room,
        participant=participant,
        track=track,
    )

    # Start streaming transcription
    stt_stream = stt_service.stream()
    asyncio.create_task(_forward_transcription(stt_stream, stt_forwarder))

    # Push audio frames to the STT service
    async for ev in audio_stream:
        stt_stream.push_frame(ev.frame)
