import React, { useState, useEffect } from 'react';

interface EditableSliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  formatDisplay?: (value: number) => string;
  helpText?: string;
  title?: string;
  autoLabel?: string;
}

export const EditableSlider: React.FC<EditableSliderProps> = ({
  label,
  value,
  min,
  max,
  step,
  onChange,
  formatDisplay,
  helpText,
  title = '',
  autoLabel = 'Auto',
}) => {
  const [inputValue, setInputValue] = useState(value.toString());
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (!isEditing) {
      setInputValue(value.toString());
    }
  }, [value, isEditing]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleInputBlur = () => {
    setIsEditing(false);
    const numValue = parseFloat(inputValue);
    if (!isNaN(numValue)) {
      const clampedValue = Math.max(min, Math.min(max, numValue));
      onChange(clampedValue);
      setInputValue(clampedValue.toString());
    } else {
      setInputValue(value.toString());
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleInputBlur();
    } else if (e.key === 'Escape') {
      setInputValue(value.toString());
      setIsEditing(false);
    }
  };

  const displayValue = formatDisplay ? formatDisplay(value) : (value === min && autoLabel ? autoLabel : value.toString());

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-medium text-zinc-700 dark:text-zinc-300" title={title}>{label}</label>
        {isEditing ? (
          <input
            type="number"
            value={inputValue}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            onKeyDown={handleInputKeyDown}
            onFocus={() => setIsEditing(true)}
            min={min}
            max={max}
            step={step}
            autoFocus
            className="text-xs font-mono text-zinc-900 dark:text-white bg-white dark:bg-zinc-800 border border-pink-500 px-2 py-0.5 rounded-lg w-20 text-right shadow-sm focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
          />
        ) : (
          <span
            onClick={() => setIsEditing(true)}
            className="text-xs font-mono text-zinc-700 dark:text-zinc-200 bg-gradient-to-r from-zinc-50 to-zinc-100 dark:from-zinc-800 dark:to-zinc-900 border border-zinc-200 dark:border-zinc-700 px-2.5 py-1 rounded-lg cursor-pointer hover:from-zinc-100 hover:to-zinc-200 dark:hover:from-zinc-700 dark:hover:to-zinc-800 transition-all shadow-sm"
          >
            {displayValue}
          </span>
        )}
      </div>
      <div className="relative h-2 bg-gradient-to-r from-zinc-100 via-zinc-200 to-zinc-100 dark:from-zinc-800 dark:via-zinc-700 dark:to-zinc-800 rounded-full shadow-inner">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <div 
          className="absolute top-0 left-0 h-full bg-gradient-to-r from-pink-400 to-rose-500 dark:from-pink-500 dark:to-rose-600 rounded-full pointer-events-none transition-all duration-150"
          style={{ width: `${((value - min) / (max - min)) * 100}%` }}
        />
        <div 
          className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white dark:bg-zinc-200 rounded-full shadow-md border-2 border-pink-500 pointer-events-none transition-all duration-150"
          style={{ left: `calc(${((value - min) / (max - min)) * 100}% - 8px)` }}
        />
      </div>
      {helpText && (
        <p className="text-[10px] text-zinc-500">{helpText}</p>
      )}
    </div>
  );
};
