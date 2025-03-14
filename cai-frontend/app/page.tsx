"use client";

import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  return (
    <main className="h-screen w-screen flex flex-col items-center justify-center bg-gradient-to-r from-gray-800 via-gray-900 to-black text-white overflow-hidden">
      <h1 className="text-6xl font-extrabold mb-4 tracking-widest">
        🌍 Speak Any Language, Effortlessly
      </h1>

      <h2 className="text-2xl mb-6 italic text-gray-400">
        Your AI-Powered Multilingual Assistant
      </h2>

      <button
        className="px-8 py-4 bg-gray-700 text-white font-bold rounded-lg shadow-lg hover:bg-gray-600 transition duration-300"
        onClick={() => router.push('/chatbot')}
      >
        Let’s Start the Conversation 🚀
      </button>
    </main>
  );
}