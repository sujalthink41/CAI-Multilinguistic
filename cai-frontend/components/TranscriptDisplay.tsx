"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import { motion } from "framer-motion";
import {
  useConnectionState,
  useMaybeRoomContext,
} from "@livekit/components-react";
import {
  ConnectionState,
  Participant,
  RoomEvent,
  TrackPublication,
  TranscriptionSegment,
} from "livekit-client";

// Custom hook to manage transcription events
function useTranscriber() {
  const state = useConnectionState();
  const room = useMaybeRoomContext();
  const [transcriptions, setTranscriptions] = useState([]);

  useEffect(() => {
    if (state === ConnectionState.Disconnected) {
      setTranscriptions([]);
    }
  }, [state]);

  useEffect(() => {
    if (!room) return;

    const updateTranscriptions = (
      segments,
      participant,
      publication
    ) => {
      const sender = participant?.identity ?? "Bot";
      const lastSegment = segments[segments.length - 1];
      const isFinal = lastSegment.final;

      setTranscriptions((prev) => {
        if (isFinal) {
          return [
            ...prev,
            { id: lastSegment.id, sender, message: lastSegment.text },
          ];
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
  const transcriptionEndRef = useRef(null);
  const [isTyping, setIsTyping] = useState(false);
  const [displayedMessages, setDisplayedMessages] = useState([]);

  // Format the incoming transcription segments
  useEffect(() => {
    if (transcriptions.length > 0) {
      const lastMessage = transcriptions[transcriptions.length - 1];
      setIsTyping(true);

      let currentIndex = 0;
      const interval = setInterval(() => {
        if (currentIndex < lastMessage.message.length) {
          setDisplayedMessages((prev) => {
            const updatedMessages = [...prev];
            const existingMessage = updatedMessages.find(
              (msg) => msg.id === lastMessage.id
            );

            if (existingMessage) {
              existingMessage.message += lastMessage.message[currentIndex];
            } else {
              updatedMessages.push({ ...lastMessage, message: lastMessage.message[currentIndex] });
            }
            return updatedMessages;
          });
          currentIndex++;
        } else {
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
            className={`px-3 py-1 rounded-lg inline-block ${item.sender === "User" ? "bg-blue-500" : "bg-green-500"}`}
          >
            <strong>{item.sender}:</strong> {item.message}
          </span>
        </div>
      ))}
      {isTyping && (
        <div className="italic text-gray-400 text-left">
          Bot is typing...
        </div>
      )}
      <div ref={transcriptionEndRef} className="h-2" />
    </div>
  );
}