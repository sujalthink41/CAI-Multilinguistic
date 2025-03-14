import React, { useState } from "react";
import { motion } from "framer-motion";

// Define the type for the language selection callback
interface LanguageSelectionProps {
  onSelectLanguage: (language: string) => void;
}

const languages = [
  { code: "en", label: "English" },
  { code: "hi", label: "Hindi" },
  { code: "fr", label: "French" },
  { code: "es", label: "Spanish" },
  { code: "de", label: "German" },
  { code: "zh", label: "Chinese" },
];

const LanguageSelection: React.FC<LanguageSelectionProps> = ({ onSelectLanguage }) => {
  const [selectedLanguage, setSelectedLanguage] = useState("en");

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedLanguage(e.target.value);
  };

  const handleStartChat = () => {
    onSelectLanguage(selectedLanguage);
  };

  return (
    <div
      className="p-6 flex flex-col items-center gap-4 rounded-lg shadow-lg"
    >
      <h2 className="text-2xl font-bold text-white mb-2">Select Your Language</h2>
      <select
        className="p-3 border-none rounded-md shadow-md w-64 bg-white text-gray-700 text-lg outline-none hover:shadow-lg transition-all"
        value={selectedLanguage}
        onChange={handleLanguageChange}
      >
        {languages.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.label}
          </option>
        ))}
      </select>
      <button
  onClick={handleStartChat}
  className="px-6 py-2 rounded-full bg-yellow-400 text-gray-800 font-semibold hover:bg-yellow-300 shadow-md hover:shadow-lg transition-all"
>
  Start Chat in {languages.find((l) => l.code === selectedLanguage)?.label || "Selected Language"}
</button>
    </div>
  );
};

export default LanguageSelection;