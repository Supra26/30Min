import React from 'react';
import { Clock, Zap, Target, Star, BookOpen } from 'lucide-react';

interface TimeSelectorProps {
  selectedTime: number | null;
  onTimeSelect: (time: number) => void;
}

export const TimeSelector: React.FC<TimeSelectorProps> = ({
  selectedTime,
  onTimeSelect,
}) => {
  const timeOptions = [
    {
      minutes: 10,
      title: 'Quick Review',
      description: 'Essential highlights and key points',
      icon: Zap,
      color: 'from-[#3BE8B0] to-[#2BC8A0]',
      bgColor: 'bg-[#0B0F1A]/60',
      borderColor: 'border-[#2B3A55]',
      textColor: 'text-[#3BE8B0]',
    },
    {
      minutes: 20,
      title: 'Focused Study',
      description: 'Core concepts with detailed summaries',
      icon: Target,
      color: 'from-[#7AA0FF] to-[#5ED3F3]',
      bgColor: 'bg-[#0B0F1A]/60',
      borderColor: 'border-[#2B3A55]',
      textColor: 'text-[#7AA0FF]',
    },
    {
      minutes: 30,
      title: 'Deep Dive',
      description: 'Comprehensive analysis with quiz',
      icon: Star,
      color: 'from-[#D877F9] to-[#B85EF3]',
      bgColor: 'bg-[#0B0F1A]/60',
      borderColor: 'border-[#2B3A55]',
      textColor: 'text-[#D877F9]',
    },
    {
      minutes: 60,
      title: 'Master Class',
      description: 'Complete understanding with minimal summarization',
      icon: BookOpen,
      color: 'from-[#7B61FF] to-[#5ED3F3]',
      bgColor: 'bg-[#0B0F1A]/60',
      borderColor: 'border-[#2B3A55]',
      textColor: 'text-[#7B61FF]',
    },
  ];

  return (
    <div className="w-full max-w-6xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-white mb-2">
          How much time do you have?
        </h2>
        <p className="text-[#BFC9D9]">
          Choose your study session length for a personalized experience
        </p>
      </div>
      
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {timeOptions.map((option) => {
          const Icon = option.icon;
          const isSelected = selectedTime === option.minutes;
          
          return (
            <button
              key={option.minutes}
              onClick={() => onTimeSelect(option.minutes)}
              className={`relative p-6 rounded-2xl border-2 transition-all duration-300 transform hover:scale-105 backdrop-blur-xl ${
                isSelected
                  ? `border-transparent bg-gradient-to-br ${option.color} text-white shadow-[0_0_20px_rgba(123,97,255,0.3)]`
                  : `${option.borderColor} ${option.bgColor} hover:border-[#7B61FF]/50 hover:shadow-[0_0_15px_rgba(123,97,255,0.2)]`
              }`}
            >
              <div className="flex flex-col items-center text-center space-y-4">
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg ${
                  isSelected ? 'bg-white/20' : `bg-gradient-to-br ${option.color}`
                }`}>
                  <Icon className="w-8 h-8 text-white" />
                </div>
                
                <div className="flex items-center space-x-2">
                  <Clock className={`w-5 h-5 ${
                    isSelected ? 'text-white' : option.textColor
                  }`} />
                  <span className={`text-2xl font-bold ${
                    isSelected ? 'text-white' : option.textColor
                  }`}>
                    {option.minutes}
                  </span>
                  <span className={`text-sm ${
                    isSelected ? 'text-white/90' : 'text-[#BFC9D9]'
                  }`}>
                    min
                  </span>
                </div>
                
                <div>
                  <h3 className={`font-semibold mb-2 ${
                    isSelected ? 'text-white' : 'text-white'
                  }`}>
                    {option.title}
                  </h3>
                  <p className={`text-sm ${
                    isSelected ? 'text-white/90' : 'text-[#BFC9D9]'
                  }`}>
                    {option.description}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};