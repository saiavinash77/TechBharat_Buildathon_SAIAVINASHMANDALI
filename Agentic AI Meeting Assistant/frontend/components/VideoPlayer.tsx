'use client'

import { useState, useRef, useEffect } from 'react'
import { Play, Pause, Volume2, Maximize, MessageSquare } from 'lucide-react'
import { Button } from './ui/button'

interface VideoPlayerProps {
  videoUrl: string
  transcript?: { time: number; text: string; speaker?: string }[]
}

export function VideoPlayer({ videoUrl, transcript = [] }: VideoPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)
  const [showTranscript, setShowTranscript] = useState(true)
  const [activeTranscriptIndex, setActiveTranscriptIndex] = useState(-1)
  
  const videoRef = useRef<HTMLVideoElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime)
      
      // Find active transcript
      const activeIndex = transcript.findIndex(
        (item, idx) => {
          const nextItem = transcript[idx + 1]
          return currentTime >= item.time && (!nextItem || currentTime < nextItem.time)
        }
      )
      setActiveTranscriptIndex(activeIndex)
    }
  }

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration)
    }
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value)
    if (videoRef.current) {
      videoRef.current.currentTime = time
      setCurrentTime(time)
    }
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const vol = parseFloat(e.target.value)
    setVolume(vol)
    if (videoRef.current) {
      videoRef.current.volume = vol
    }
  }

  const handleTranscriptClick = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time
      setCurrentTime(time)
      if (!isPlaying) {
        videoRef.current.play()
        setIsPlaying(true)
      }
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const toggleFullscreen = () => {
    if (containerRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen()
      } else {
        containerRef.current.requestFullscreen()
      }
    }
  }

  return (
    <div ref={containerRef} className="relative bg-black rounded-2xl overflow-hidden">
      <video
        ref={videoRef}
        src={videoUrl}
        className="w-full aspect-video object-contain"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
      />

      {/* Video Controls */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
        {/* Progress Bar */}
        <input
          type="range"
          min="0"
          max={duration || 100}
          value={currentTime}
          onChange={handleSeek}
          className="w-full h-1 bg-white/30 rounded-full appearance-none cursor-pointer mb-4"
          style={{
            background: `linear-gradient(to right, #3B82F6 ${(currentTime / (duration || 1)) * 100}%, rgba(255,255,255,0.3) 0%)`
          }}
        />

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={togglePlay}
              className="text-white hover:bg-white/20"
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </Button>

            <div className="flex items-center gap-2">
              <Volume2 className="w-4 h-4 text-white" />
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={volume}
                onChange={handleVolumeChange}
                className="w-20 h-1 bg-white/30 rounded-full appearance-none cursor-pointer"
              />
            </div>

            <span className="text-white text-sm">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowTranscript(!showTranscript)}
              className={`text-white hover:bg-white/20 ${showTranscript ? 'bg-white/20' : ''}`}
            >
              <MessageSquare className="w-5 h-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleFullscreen}
              className="text-white hover:bg-white/20"
            >
              <Maximize className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </div>

      {/* Transcript Overlay */}
      {showTranscript && transcript.length > 0 && (
        <div className="absolute right-4 top-4 bottom-24 w-80 max-h-[calc(100%-8rem)] overflow-y-auto bg-black/70 backdrop-blur-sm rounded-xl p-4">
          <h4 className="text-white font-semibold mb-3 sticky top-0 bg-black/70 backdrop-blur-sm py-2">
            Transcript
          </h4>
          <div className="space-y-3">
            {transcript.map((item, idx) => (
              <div
                key={idx}
                onClick={() => handleTranscriptClick(item.time)}
                className={`p-3 rounded-lg cursor-pointer transition-all ${
                  idx === activeTranscriptIndex
                    ? 'bg-primary/30 border border-primary'
                    : 'bg-white/10 hover:bg-white/20'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-white/60">{formatTime(item.time)}</span>
                  {item.speaker && (
                    <span className="text-xs font-medium text-primary">{item.speaker}</span>
                  )}
                </div>
                <p className="text-sm text-white/90">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
