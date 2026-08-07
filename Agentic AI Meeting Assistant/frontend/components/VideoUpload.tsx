'use client'

import { useState, useRef } from 'react'
import { Upload, X, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from './ui/button'
import { uploadMedia } from '@/lib/api'

interface VideoUploadProps {
  onVideoUploaded: (videoData: { file: File; url: string; meetingId: string; reviewData: any }) => void
}

export function VideoUpload({ onVideoUploaded }: VideoUploadProps) {
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'gcs_streaming' | 'groq_processing' | 'complete' | 'error'>('idle')
  const [uploadStatus, setUploadStatus] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [videoUrl, setVideoUrl] = useState<string>('')
  const [error, setError] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type.startsWith('video/')) {
      setVideoFile(file)
      setUploadState('uploading')
      setError('')
      await uploadVideo(file)
    } else {
      setError('Please select a valid video file')
      setUploadState('error')
    }
  }

  const uploadVideo = async (file: File) => {
    try {
      setUploadState('uploading')
      setUploadStatus('Uploading video...')
      setUploadProgress(10)
      
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) return prev
          return prev + 10
        })
      }, 500)
      
      const meetingData = await uploadMedia(file, (progress) => {
        setUploadProgress(progress)
        if (progress >= 50 && progress < 80) {
          setUploadState('groq_processing')
          setUploadStatus('Processing with Groq Whisper...')
        } else if (progress >= 80) {
          setUploadStatus('Extracting action items...')
        }
      })
      
      clearInterval(progressInterval)
      
      setUploadProgress(100)
      setUploadStatus('Complete')
      const url = URL.createObjectURL(file)
      setVideoUrl(url)
      setUploadState('complete')
      onVideoUploaded({ file, url, meetingId: meetingData.meeting_id, reviewData: meetingData.review })

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed'
      
      if (errorMessage.includes('SSL') || errorMessage.includes('timeout') || errorMessage.includes('GCS')) {
        setError('Cloud storage upload failed. This might be a network issue. Please try again or check your connection.')
      } else if (errorMessage.includes('timed out')) {
        setError(errorMessage)
      } else if (errorMessage.includes('503') || errorMessage.includes('502')) {
        setError('Server temporarily unavailable. Please check if backend services (GCS, Groq, InsForge) are properly configured.')
      } else {
        setError(errorMessage)
      }
      
      setUploadState('error')
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith('video/')) {
      setVideoFile(file)
      setUploadState('uploading')
      setError('')
      uploadVideo(file)
    } else {
      setError('Please drop a valid video file')
      setUploadState('error')
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const resetUpload = () => {
    setUploadState('idle')
    setUploadProgress(0)
    setVideoFile(null)
    setVideoUrl('')
    setError('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      {uploadState === 'idle' && (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="border-2 border-dashed border-gray-300 rounded-2xl p-16 text-center cursor-pointer hover:border-[#C9A0DC] hover:bg-[#F3E5F8]/30 transition-all group"
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            onChange={handleFileSelect}
            className="hidden"
          />
          <div className="flex flex-col items-center gap-4">
            <div className="w-20 h-20 rounded-full bg-[#F3E5F8] flex items-center justify-center group-hover:scale-110 transition-transform">
              <Upload className="w-10 h-10 text-[#C9A0DC]" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Upload your meeting video
              </h3>
              <p className="text-gray-600">
                Drag and drop or click to browse
              </p>
              <p className="text-gray-600 text-sm mt-1">
                Supports MP4, WebM, MOV (max 500MB)
              </p>
            </div>
          </div>
        </div>
      )}

      {(uploadState === 'uploading' || uploadState === 'gcs_streaming' || uploadState === 'groq_processing') && (
        <div className="bg-white border border-gray-200 rounded-2xl p-8">
          <div className="flex items-center gap-4 mb-6">
            <Loader2 className="w-8 h-8 text-[#C9A0DC] animate-spin" />
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">{uploadStatus || 'Processing...'}</h3>
              <p className="text-sm text-gray-600">{videoFile?.name}</p>
            </div>
            <Button variant="outline" size="sm" onClick={resetUpload}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
            <div
              className="bg-[#C9A0DC] h-full transition-all duration-300 ease-out"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 mt-2 text-right">
            {Math.round(uploadProgress)}%
          </p>
          <div className="space-y-3 mt-6">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="text-sm text-gray-600">Video file selected</span>
            </div>
            {uploadState === 'gcs_streaming' || uploadState === 'groq_processing' ? (
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-sm text-gray-600">Streaming to GCS</span>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Loader2 className="w-5 h-5 text-[#C9A0DC] animate-spin" />
                <span className="text-sm text-gray-600">Streaming to GCS...</span>
              </div>
            )}
            {uploadState === 'groq_processing' ? (
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-sm text-gray-600">Processing with Groq Whisper</span>
              </div>
            ) : uploadState === 'gcs_streaming' ? (
              <div className="flex items-center gap-3">
                <Loader2 className="w-5 h-5 text-[#C9A0DC] animate-spin" />
                <span className="text-sm text-gray-600">Processing with Groq Whisper...</span>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
                <span className="text-sm text-gray-600">Processing with Groq Whisper</span>
              </div>
            )}
            {uploadState === 'groq_processing' ? (
              <div className="flex items-center gap-3">
                <Loader2 className="w-5 h-5 text-[#C9A0DC] animate-spin" />
                <span className="text-sm text-gray-600">Extracting action items...</span>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
                <span className="text-sm text-gray-600">Extracting action items</span>
              </div>
            )}
          </div>
        </div>
      )}

      {uploadState === 'complete' && (
        <div className="bg-white border border-gray-200 rounded-2xl p-8">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-500" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900">Video processed successfully</h3>
              <p className="text-sm text-gray-600">{videoFile?.name}</p>
            </div>
            <Button onClick={resetUpload}>
              Upload New Video
            </Button>
          </div>
          <div className="aspect-video bg-gray-100 rounded-xl overflow-hidden">
            <video
              src={videoUrl}
              controls
              className="w-full h-full object-contain"
            />
          </div>
        </div>
      )}

      {uploadState === 'error' && (
        <div className="bg-orange-50 border border-orange-200 rounded-2xl p-8">
          <div className="flex items-center gap-4">
            <AlertCircle className="w-8 h-8 text-orange-500" />
            <div className="flex-1">
              <h3 className="font-semibold text-orange-700">Upload failed</h3>
              <p className="text-sm text-orange-600">{error}</p>
            </div>
            <Button variant="outline" onClick={resetUpload}>
              Try Again
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
