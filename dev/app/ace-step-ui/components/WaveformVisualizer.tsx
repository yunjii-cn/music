import React, { useEffect, useRef, useState } from 'react';

interface WaveformVisualizerProps {
  audioUrl: string | null;
  currentTime: number;
  duration: number;
  progressBarRef?: React.RefObject<HTMLDivElement>;
  onSeek: (time: number) => void;
}

interface WaveformData {
  peaks: number[];
  length: number;
}

export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
  audioUrl,
  currentTime,
  duration,
  progressBarRef,
  onSeek,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [waveformData, setWaveformData] = useState<WaveformData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Generate waveform data from audio file
  useEffect(() => {
    if (!audioUrl) {
      setWaveformData(null);
      return;
    }

    setIsLoading(true);
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    
    fetch(audioUrl)
      .then(response => {
        if (!response.ok) throw new Error('Failed to fetch audio');
        return response.arrayBuffer();
      })
      .then(arrayBuffer => audioContext.decodeAudioData(arrayBuffer))
      .then(audioBuffer => {
        const channelData = audioBuffer.getChannelData(0);
        // More samples for finer bars
        const samples = Math.min(800, Math.floor(canvasRef.current?.clientWidth || 600));
        const blockSize = Math.floor(channelData.length / samples);
        const peaks: number[] = [];
        
        for (let i = 0; i < samples; i++) {
          let peak = 0;
          for (let j = 0; j < blockSize; j++) {
            const sample = Math.abs(channelData[i * blockSize + j] || 0);
            if (sample > peak) peak = sample;
          }
          peaks.push(peak);
        }
        
        setWaveformData({ peaks, length: audioBuffer.duration });
        setIsLoading(false);
      })
      .catch(error => {
        console.error('Failed to generate waveform:', error);
        setIsLoading(false);
      });

    return () => {
      audioContext.close();
    };
  }, [audioUrl]);

  // Draw waveform
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !waveformData) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    const centerY = height / 2;
    
    // Very thin bars with small gap - like SoundCloud
    const barWidth = 2;
    const gap = 1;
    const totalBars = waveformData.peaks.length;
    const playedPercent = duration > 0 ? Math.max(0, Math.min(1, currentTime / duration)) : 0;
    
    // Calculate exact pixel position for played boundary (matching the progress line)
    const playedPixelWidth = playedPercent * width;

    // Detect dark mode from parent element
    const parentEl = canvas.parentElement;
    const isDarkMode = parentEl ? window.getComputedStyle(parentEl).backgroundColor.includes('28') || 
                                   document.documentElement.classList.contains('dark') : false;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw waveform bars
    waveformData.peaks.forEach((peak, index) => {
      // Smooth the peak with neighboring values for cleaner look
      const smoothedPeak = index > 0 && index < totalBars - 1
        ? (peak + waveformData.peaks[index - 1] + waveformData.peaks[index + 1]) / 3
        : peak;
      
      // Scale to height with minimum visible size
      const barHeight = Math.max(3, smoothedPeak * (height - 8));
      const x = index * (barWidth + gap);
      const barEndX = x + barWidth;
      
      // Determine if bar is played based on exact pixel position
      // A bar is considered played if its center is before the played position
      const barCenterX = x + barWidth / 2;
      const isPlayed = barCenterX <= playedPixelWidth;

      // Theme-aware colors
      if (isPlayed) {
        // Played - warm coral/pink gradient (same for both themes)
        const gradient = ctx.createLinearGradient(0, centerY - barHeight/2, 0, centerY + barHeight/2);
        gradient.addColorStop(0, '#f43f5e');
        gradient.addColorStop(0.5, '#ec4899');
        gradient.addColorStop(1, '#f43f5e');
        ctx.fillStyle = gradient;
      } else {
        // Unplayed - theme aware
        // Light mode: darker gray for visibility
        // Dark mode: lighter gray
        ctx.fillStyle = isDarkMode ? 'rgba(160, 160, 170, 0.4)' : 'rgba(100, 100, 110, 0.35)';
      }

      // Draw rounded bar
      const barH = Math.min(barHeight, height - 4);
      const y = centerY - barH / 2;
      
      ctx.beginPath();
      ctx.roundRect(x, y, barWidth, barH, 1);
      ctx.fill();
    });
  }, [waveformData, currentTime, duration]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!duration) return;
    
    // Use progressBarRef if available for consistent calculation
    const container = progressBarRef?.current || canvasRef.current;
    if (!container) return;
    
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percent = Math.max(0, Math.min(1, x / rect.width));
    onSeek(percent * duration);
  };

  if (isLoading || !waveformData) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="w-full h-0.5 bg-zinc-300/20 dark:bg-zinc-600/20" />
      </div>
    );
  }

  return (
    <canvas
      ref={canvasRef}
      onClick={handleClick}
      className="w-full h-full cursor-pointer"
      style={{ width: '100%', height: '100%' }}
    />
  );
};
