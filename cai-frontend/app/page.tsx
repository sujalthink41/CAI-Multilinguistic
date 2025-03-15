"use client";
import React from "react";
import { motion } from "framer-motion";
import { Bot, ArrowRight, MessageSquare, Globe, Brain, Zap } from "lucide-react";
import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white overflow-hidden">
      {/* Hero Section with Dynamic Background */}
      <div className="relative">
        {/* Animated Background Grid */}
        <div className="absolute inset-0 grid grid-cols-8 grid-rows-8">
          {[...Array(64)].map((_, i) => (
            <motion.div
              key={i}
              className="border-[0.5px] border-purple-500/5"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.02 }}
            />
          ))}
        </div>

        {/* Navigation */}
        <nav className="fixed top-0 w-full z-50 bg-black/10 backdrop-blur-lg border-b border-white/10">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2"
            >
              <Bot className="w-8 h-8 text-purple-400" />
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-blue-400">
                ConversAI
              </span>
            </motion.div>
            {/* <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-6"
            >
              <Link href="/chatbot" className="px-6 py-2 rounded-full bg-purple-500 hover:bg-purple-600 transition-all text-white flex items-center gap-2">
                Lets Talk <ArrowRight className="w-4 h-4" />
              </Link>
            </motion.div> */}
          </div>
        </nav>

        {/* Hero Content */}
        <div className="relative pt-32 pb-20 container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="max-w-4xl mx-auto text-center"
          >
            <h1 className="text-8xl font-bold mb-6 leading-tight">
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-400 via-blue-400 to-purple-400 animate-gradient">
                Next Generation AI Conversations
              </span>
            </h1>
            <p className="text-xl text-gray-400 mb-12 leading-relaxed">
              Experience natural multilingual conversations powered by advanced artificial intelligence.
              Seamlessly switch between languages and enjoy human-like interactions.
            </p>
            <div className="flex gap-6 justify-center">
              <Link
                href="/chatbot"
                className="group px-8 py-4 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full text-white font-semibold hover:from-purple-600 hover:to-blue-600 transition-all transform hover:scale-105 flex items-center gap-3"
              >
                Lest Talk
                <motion.span animate={{ y: [5, 0, 5], }} transition={{ repeat: Infinity, duration: 1.5 }}>
                <Bot className="w-7 h-7" />
                </motion.span>
              </Link>
            </div>
          </motion.div>

          {/* Floating 3D Objects */}
          <div className="absolute inset-0 pointer-events-none">
            {[...Array(20)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-2 h-2 bg-purple-500/20 rounded-full"
                animate={{
                  x: [Math.random() * window.innerWidth, Math.random() * window.innerWidth],
                  y: [Math.random() * window.innerHeight, Math.random() * window.innerHeight],
                  scale: [1, 1.5, 1],
                }}
                transition={{
                  duration: Math.random() * 10 + 10,
                  repeat: Infinity,
                  repeatType: "reverse",
                }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <section className="py-20 bg-[#0D0D12]">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="grid md:grid-cols-3 gap-8"
          >
            <FeatureCard
              icon={<Globe className="w-8 h-8 text-purple-400" />}
              title="Multilingual Support"
              description="Seamlessly switch between languages during conversations with natural transitions"
            />
            <FeatureCard
              icon={<Brain className="w-8 h-8 text-blue-400" />}
              title="Advanced AI"
              description="Powered by state-of-the-art language models for human-like interactions"
            />
            <FeatureCard
              icon={<Zap className="w-8 h-8 text-purple-400" />}
              title="Real-time Processing"
              description="Lightning-fast responses with instant language detection and translation"
            />
          </motion.div>
        </div>
      </section>
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <motion.div whileHover={{ scale: 1.05 }} className="p-8 rounded-2xl bg-[#1A1A1F] backdrop-blur-lg border border-white/10">
      <div className="mb-6">{icon}</div>
      <h3 className="text-2xl font-semibold text-white mb-4">{title}</h3>
      <p className="text-gray-400">{description}</p>
    </motion.div>
  );
}
