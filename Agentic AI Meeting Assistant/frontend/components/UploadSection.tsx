'use client'

import { useState } from 'react'
import { Upload, FileText, Video } from 'lucide-react'
import { Card, CardContent } from './ui/card'
import { Button } from './ui/button'
import { Textarea } from './ui/textarea'
import { ingestText, ingestFile, uploadMedia } from '@/lib/api'
import type { MeetingData } from '@/lib/api'

interface UploadSectionProps {
  onMeetingAnalyzed: (data: MeetingData) => void
}

export function UploadSection({ onMeetingAnalyzed }: UploadSectionProps) {
  const [activeTab, setActiveTab] = useState<'text' | 'file' | 'media'>('text')
  const [textTranscript, setTextTranscript] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStatus, setUploadStatus] = useState('')

  const handleAnalyzeText = async () => {
    if (textTranscript.length < 50) {
      alert('Need at least 50 characters.')
      return
    }
    setIsAnalyzing(true)
    try {
      const data = await ingestText({
        transcript: textTranscript,
        meeting_date: new Date().toISOString().split('T')[0],
        title: 'Pasted transcript',
      })
      onMeetingAnalyzed(data)
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Analysis failed')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleFileUpload = async (file: File) => {
    setIsAnalyzing(true)
    try {
      const data = await ingestFile(file)
      onMeetingAnalyzed(data)
    } catch (error) {
      alert(error instanceof Error ? error.message : 'File upload failed')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleMediaUpload = async (file: File) => {
    setIsAnalyzing(true)
    setUploadStatus('Uploading...')
    try {
      const data = await uploadMedia(file, (progress) => {
        setUploadProgress(progress)
        setUploadStatus(`Uploading ${progress}%`)
      })
      setUploadStatus('Done.')
      onMeetingAnalyzed(data)
    } catch (error) {
      setUploadStatus('Error: ' + (error instanceof Error ? error.message : 'Upload failed'))
    } finally {
      setIsAnalyzing(false)
      setUploadProgress(0)
    }
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex border-b border-border mb-6">
          <button
            onClick={() => setActiveTab('text')}
            className={`px-6 py-3 text-sm font-medium transition-colors relative ${
              activeTab === 'text' ? 'text-text-primary' : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            Paste transcript
            {activeTab === 'text' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('file')}
            className={`px-6 py-3 text-sm font-medium transition-colors relative ${
              activeTab === 'file' ? 'text-text-primary' : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            Upload .txt / .vtt / .srt
            {activeTab === 'file' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
            )}
          </button>
          <button
            onClick={() => setActiveTab('media')}
            className={`px-6 py-3 text-sm font-medium transition-colors relative ${
              activeTab === 'media' ? 'text-text-primary' : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            Upload audio/video
            {activeTab === 'media' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
            )}
          </button>
        </div>

        {activeTab === 'text' && (
          <div>
            <Textarea
              placeholder="Paste meeting transcript (speaker labels help)..."
              value={textTranscript}
              onChange={(e) => setTextTranscript(e.target.value)}
              disabled={isAnalyzing}
            />
            <div className="mt-4 text-right">
              <Button onClick={handleAnalyzeText} disabled={isAnalyzing}>
                {isAnalyzing ? 'Analyzing...' : 'Analyze'}
              </Button>
            </div>
          </div>
        )}

        {activeTab === 'file' && (
          <div>
            <label className="block">
              <div className="border-2 border-dashed border-border rounded-lg p-12 text-center cursor-pointer hover:border-primary hover:bg-primary/5 transition-all">
                <FileText className="mx-auto h-12 w-12 text-text-secondary mb-4" />
                <p className="text-text-secondary">Click to upload .txt, .vtt, or .srt</p>
                <input
                  type="file"
                  className="hidden"
                  accept=".txt,.vtt,.srt"
                  onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                  disabled={isAnalyzing}
                />
              </div>
            </label>
          </div>
        )}

        {activeTab === 'media' && (
          <div>
            <label className="block">
              <div className="border-2 border-dashed border-border rounded-lg p-12 text-center cursor-pointer hover:border-primary hover:bg-primary/5 transition-all">
                <Video className="mx-auto h-12 w-12 text-text-secondary mb-4" />
                <p className="text-text-secondary">Click to upload MP3 / MP4 / WebM (or drag here)</p>
                <input
                  type="file"
                  className="hidden"
                  accept="audio/*,video/*"
                  onChange={(e) => e.target.files?.[0] && handleMediaUpload(e.target.files[0])}
                  disabled={isAnalyzing}
                />
              </div>
            </label>
            {uploadProgress > 0 && (
              <div className="mt-4">
                <div className="h-1 bg-border rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="text-sm text-text-secondary mt-2">{uploadStatus}</p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
