import { motion } from 'framer-motion';
import { Globe } from 'lucide-react';
import { cn } from '../lib/utils';

const languages = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'हिंदी' },
  { code: 'ta', name: 'தமிழ்' },
  { code: 'te', name: 'తెలుగు' },
];

interface LanguageSelectorProps {
  selectedLanguage: string;
  onLanguageChange: (code: string) => void;
}

export function LanguageSelector({ selectedLanguage, onLanguageChange }: LanguageSelectorProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative group"
    >
      <button className="flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-lg rounded-full text-white hover:bg-white/20 transition-all">
        <Globe className="w-4 h-4" />
        <span>{languages.find(l => l.code === selectedLanguage)?.name}</span>
      </button>
      
      <div className="absolute right-0 mt-2 w-48 py-2 bg-white/10 backdrop-blur-lg rounded-xl shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
        {languages.map((lang) => (
          <button
            key={lang.code}
            onClick={() => onLanguageChange(lang.code)}
            className={cn(
              "w-full px-4 py-2 text-left text-white hover:bg-white/20 transition-all",
              selectedLanguage === lang.code && "bg-white/20"
            )}
          >
            {lang.name}
          </button>
        ))}
      </div>
    </motion.div>
  );
}