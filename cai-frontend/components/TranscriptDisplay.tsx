"use client";

import { useEffect, useState, useRef } from "react";
import { useConnectionState, useMaybeRoomContext } from "@livekit/components-react";
import {
  ConnectionState,
  Participant,
  Room,
  RoomEvent,
  TrackPublication,
  TranscriptionSegment,
} from "livekit-client";

// Custom hook to manage transcription events
function useTranscriber() {
  const state = useConnectionState();
  const room = useMaybeRoomContext();
  const [transcriptions, setTranscriptions] = useState<
    { id: string; sender: string; message: string }[]
  >([]);

  useEffect(() => {
    if (state === ConnectionState.Disconnected) {
      setTranscriptions([]);
    }
  }, [state]);

  useEffect(() => {
    if (!room) return;

    const updateTranscriptions = (
      segments: TranscriptionSegment[],
      participant?: Participant,
      publication?: TrackPublication
    ) => {
      if (!segments.length) return;

      const sender = participant?.identity ?? "Bot";
      const lastSegment = segments[segments.length - 1];

      setTranscriptions((prev) => {
        if (lastSegment.final) {
          return [...prev, { id: lastSegment.id, sender, message: lastSegment.text }];
        }
        return prev;
      });
    };

    room.on(RoomEvent.TranscriptionReceived, updateTranscriptions);
    return () => room.off(RoomEvent.TranscriptionReceived, updateTranscriptions);
  }, [room, state]);

  return { state, transcriptions };
}

// Typewriter + Chat Bubble Component
export default function TranscriptDisplay({ typingSpeed = 50 }) {
  const { state, transcriptions } = useTranscriber();
  const transcriptionEndRef = useRef<HTMLDivElement>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [displayedMessages, setDisplayedMessages] = useState<
    { id: string; sender: string; message: string }[]
  >([]);

  // Format the incoming transcription segments
  useEffect(() => {
    if (transcriptions.length > 0) {
      const lastMessage = transcriptions[transcriptions.length - 1];
      setIsTyping(true);

      let currentIndex = 0;
      const interval = setInterval(() => {
        setDisplayedMessages((prev) => {
          const updatedMessages = [...prev];
          const existingMessage = updatedMessages.find((msg) => msg.id === lastMessage.id);

          if (existingMessage) {
            return updatedMessages.map((msg) =>
              msg.id === lastMessage.id
                ? { ...msg, message: msg.message + lastMessage.message[currentIndex] }
                : msg
            );
          } else {
            return [...updatedMessages, { ...lastMessage, message: lastMessage.message[currentIndex] }];
          }
        });

        currentIndex++;

        if (currentIndex >= lastMessage.message.length) {
          setIsTyping(false);
          clearInterval(interval);
        }
      }, typingSpeed);
    }
  }, [transcriptions, typingSpeed]);

  // Scroll to the latest message
  useEffect(() => {
    transcriptionEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [displayedMessages]);

  return (
    <div className="p-4 bg-gray-800 text-white rounded-lg shadow-md h-[400px] overflow-y-auto">
      {displayedMessages.map((item) => (
        <div
          key={item.id}
          className={`mb-2 ${item.sender === "User" ? "text-right" : "text-left"}`}
        >
          <span
            className={`px-3 py-1 rounded-lg inline-block ${
              item.sender === "User" ? "bg-blue-500" : "bg-green-500"
            }`}
          >
            <strong>{item.sender}:</strong> {item.message}
          </span>
        </div>
      ))}
      {isTyping && <div className="italic text-gray-400 text-left">Bot is typing...</div>}
      <div ref={transcriptionEndRef} className="h-2" />
    </div>
  );
}
