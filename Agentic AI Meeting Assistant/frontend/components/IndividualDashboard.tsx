'use client'

import { ArrowLeft } from 'lucide-react'
import { VideoUpload } from './VideoUpload'

interface IndividualDashboardProps {
  onVideoUploaded: (data: { file: File; url: string; meetingId: string; reviewData: any }) => void
  onBack: () => void
}

export function IndividualDashboard({ onVideoUploaded, onBack }: IndividualDashboardProps) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#F3E5F8] to-white p-6">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={onBack}
          className="mb-6 flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">NOVA</h1>
          <p className="text-[#C9A0DC] font-semibold text-xl">Your Meeting Intelligence</p>
        </div>
        <VideoUpload onVideoUploaded={onVideoUploaded} />
      </div>
    </div>
  )
}
