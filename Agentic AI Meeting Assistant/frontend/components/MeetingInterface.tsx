'use client'

import { useState } from 'react'
import { VideoUpload } from './VideoUpload'
import { VideoPlayer } from './VideoPlayer'
import { QuestionAsk } from './QuestionAsk'
import { Play, MessageSquare, Calendar, FileText, AlertTriangle, Send } from 'lucide-react'
import { askQuestion } from '@/lib/api'

interface MeetingInterfaceProps {
  meetingId?: string
  videoData?: { file: File; url: string } | null
}

export function MeetingInterface({ meetingId, videoData: initialVideoData }: MeetingInterfaceProps) {
  const [videoData, setVideoData] = useState<{ file: File; url: string; meetingId: string; reviewData: any } | null>(
    initialVideoData ? { ...initialVideoData, meetingId: meetingId || '', reviewData: null } : null
  )
  const [activeTab, setActiveTab] = useState<'sections' | 'transcript' | 'qa'>('sections')
  const [currentMeetingId, setCurrentMeetingId] = useState<string | null>(meetingId || null)
  const [transcriptData, setTranscriptData] = useState<{ time: number; text: string; speaker?: string }[]>([])
  const [chatMessages, setChatMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([])
  const [chatInput, setChatInput] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)

  const handleSendMessage = async () => {
    if (!chatInput.trim() || !currentMeetingId) return

    const userMessage = chatInput.trim()
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setChatInput('')
    setIsChatLoading(true)

    try {
      const response = await askQuestion(currentMeetingId, userMessage)
      setChatMessages(prev => [...prev, { role: 'assistant', content: response.answer }])
    } catch (error) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error answering your question. Please try again.' }])
    } finally {
      setIsChatLoading(false)
    }
  }

  const handleShortcutClick = (shortcut: string) => {
    setChatInput(shortcut)
  }

  const handleVideoUploaded = (data: { file: File; url: string; meetingId: string; reviewData: any }) => {
    setVideoData(data)
    setCurrentMeetingId(data.meetingId)
    
    // Populate meeting sections with data from review if available
    if (data.reviewData?.payload) {
      const payload = data.reviewData.payload
      
      // Update talking points from decisions or summary
      if (payload.decisions?.length > 0) {
        setTalkingPoints(payload.decisions.map((decision: string, idx: string) => ({
          id: idx,
          content: decision,
          author: 'AI Extracted',
          tags: ['Decision']
        })))
      }
      
      // Update action items from items
      if (payload.items?.length > 0) {
        setActionItems(payload.items.map((item: any) => ({
          id: item.id,
          content: item.title,
          author: item.speaker_name || 'Unknown',
          tags: [item.classification]
        })))
      }
      
      // Update priorities from open questions
      if (payload.open_questions?.length > 0) {
        setPriorities(payload.open_questions.map((q: string, idx: string) => ({
          id: idx,
          content: q,
          author: 'AI Extracted',
          tags: ['Open Question']
        })))
      }
      
      // Update issues from risks/blockers
      if (payload.risks_or_blockers?.length > 0) {
        setIssues(payload.risks_or_blockers.map((risk: string, idx: string) => ({
          id: idx,
          content: risk,
          author: 'AI Extracted',
          tags: ['Risk']
        })))
      }
    }
    
    // Fetch transcript data for video player
    if (data.meetingId) {
      fetchMeetingTranscript(data.meetingId)
    }
    
    setActiveTab('sections')
  }

  const fetchMeetingTranscript = async (meetingId: string) => {
    try {
      const { getMeetingDetails } = await import('@/lib/api')
      const details = await getMeetingDetails(meetingId)
      
      // Parse transcript text into segments with timestamps from database
      if (details.meeting?.transcript_text) {
        // Try to get transcript segments from the database
        const transcriptText = details.meeting.transcript_text
        
        // If we have transcript segments in the database, use those
        if (details.meeting.transcript_segments && details.meeting.transcript_segments.length > 0) {
          const segments = details.meeting.transcript_segments.map((seg: any) => ({
            time: seg.start_seconds,
            text: seg.text,
            speaker: 'Unknown' // Speaker identification would need to be added to transcription
          }))
          setTranscriptData(segments)
        } else {
          // Fallback: parse transcript text into segments with approximate timestamps
          const segments = transcriptText.split('\n').filter(Boolean).map((line: string, idx: number) => ({
            time: idx * 5, // Approximate 5 seconds per line
            text: line,
            speaker: 'Unknown'
          }))
          setTranscriptData(segments)
        }
      }
    } catch (error) {
      console.error('Failed to fetch transcript:', error)
    }
  }

  const handleAskQuestion = async (question: string) => {
    if (!currentMeetingId) {
      return 'Please upload a video first to ask questions.'
    }
    
    try {
      const { askQuestion } = await import('@/lib/api')
      const response = await askQuestion(currentMeetingId, question)
      return response.answer
    } catch (error) {
      return 'Sorry, I encountered an error. Please try again.'
    }
  }

  // Sample data for meeting sections
  const [talkingPoints, setTalkingPoints] = useState([
    { id: '1', content: 'Q3 roadmap review and prioritization', author: 'Pascal', tags: ['Strategy'] },
    { id: '2', content: 'Team capacity planning for next sprint', author: 'Ally', tags: ['Planning'] },
    { id: '3', content: 'Customer feedback integration discussion', author: 'Lydia', tags: ['Product'] },
  ])

  const [priorities, setPriorities] = useState([
    { id: '1', content: 'Complete API integration by Friday', author: 'Pascal', tags: ['High Priority'] },
    { id: '2', content: 'Review and approve design mockups', author: 'Ally', tags: ['Design'] },
    { id: '3', content: 'Schedule user testing sessions', author: 'Lydia', tags: ['Research'] },
  ])

  const [actionItems, setActionItems] = useState([
    { id: '1', content: 'Pascal to finalize API documentation', author: 'Pascal', tags: ['Documentation'] },
    { id: '2', content: 'Ally to coordinate with design team', author: 'Ally', tags: ['Coordination'] },
  ])

  const [issues, setIssues] = useState([
    { id: '1', content: 'Deployment pipeline experiencing delays', author: 'Pascal', tags: ['Infrastructure'] },
    { id: '2', content: 'Team bandwidth constraints this week', author: 'Ally', tags: ['Resource'] },
  ])

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Weekly Team Sync</h1>
            <p className="text-sm text-gray-500">Today at 10:00 AM • 45 min</p>
          </div>
          <div className="flex gap-3">
            <button className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md transition-colors">
              Share
            </button>
            <button className="px-4 py-2 text-sm bg-[#C9A0DC] text-white rounded-md hover:bg-[#9B6DB8] transition-colors">
              Sync All to GitHub (2)
            </button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Left Panel - Main Content (8 columns) */}
        <main className="flex-1 max-w-4xl bg-white p-6">
          {!currentMeetingId ? (
            <VideoUpload onVideoUploaded={handleVideoUploaded} />
          ) : (
            <div className="space-y-6">
              {/* Video Player */}
              <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
                <VideoPlayer
                  videoUrl={videoData?.url || ''}
                  transcript={transcriptData.length > 0 ? transcriptData : [
                    { time: 0, text: 'Welcome everyone to our weekly sync', speaker: 'Pascal' },
                    { time: 5, text: 'Let\'s start with the Q3 roadmap review', speaker: 'Pascal' },
                    { time: 12, text: 'I have some updates on the API integration', speaker: 'Ally' },
                    { time: 18, text: 'The customer feedback looks promising', speaker: 'Lydia' },
                    { time: 25, text: 'We need to prioritize the deployment issues', speaker: 'Pascal' },
                  ]}
                />
              </div>

              {/* Executive Summary */}
              <div className="bg-white rounded-2xl border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-3">Executive Summary</h2>
                <p className="text-gray-700 leading-relaxed">
                  The team reviewed Q3 roadmap priorities and discussed capacity planning for the upcoming sprint. 
                  Key decisions included prioritizing API integration work and addressing deployment pipeline delays. 
                  Customer feedback integration was identified as a high-priority item for the next cycle.
                </p>
              </div>

              {/* Action Items with Checkboxes */}
              <div className="bg-white rounded-2xl border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Action Items</h2>
                <div className="space-y-3">
                  {actionItems.map((item) => (
                    <div key={item.id} className="flex items-start gap-3 p-4 bg-slate-50 rounded-2xl">
                      <div className="mt-1">
                        <input type="checkbox" className="w-5 h-5 text-[#C9A0DC] rounded-full" />
                      </div>
                      <div className="flex-1">
                        <p className="text-gray-900 font-medium">@{item.author} - {item.content}</p>
                        <span className={`inline-block mt-2 px-3 py-1 text-xs rounded-full ${
                          item.tags.includes('EXPLICIT_COMMITMENT') 
                            ? 'bg-[#C9A0DC]/20 text-[#C9A0DC]' 
                            : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {item.tags[0] || 'Needs Confirmation'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Topics & Transcript Breakdown */}
              <div className="bg-white rounded-2xl border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Topics & Transcript</h2>
                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Project updates and upcoming work</h3>
                    <div className="space-y-2">
                      {transcriptData.slice(0, 3).map((seg, idx) => (
                        <button
                          key={idx}
                          className="w-full text-left p-3 hover:bg-slate-50 rounded-2xl text-sm text-gray-700 transition-colors"
                        >
                          <span className="text-[#C9A0DC] font-mono">{Math.floor(seg.time / 60)}:{(seg.time % 60).toString().padStart(2, '0')}</span>
                          <span className="ml-2">{seg.text}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Chapter notes & timestamped quotes</h3>
                    <div className="space-y-2">
                      {talkingPoints.map((point) => (
                        <div key={point.id} className="p-4 bg-slate-50 rounded-2xl">
                          <p className="text-sm text-gray-700">{point.content}</p>
                          <p className="text-xs text-gray-500 mt-1">- {point.author}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>

        {/* Right Sidebar - AI Assistant (4 columns) */}
        <aside className="w-96 bg-white border-l border-gray-200 p-6">
          <div className="mb-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-[#C9A0DC]" />
              Ask Assistant
            </h3>
            
            {/* Shortcut Buttons */}
            <div className="grid grid-cols-2 gap-2 mb-6">
              {[
                'Coach me',
                'Open questions',
                'Prepare agenda',
                'Recap action items',
              ].map((shortcut) => (
                <button
                  key={shortcut}
                  onClick={() => handleShortcutClick(shortcut)}
                  className="px-4 py-3 text-sm bg-slate-100 hover:bg-[#F3E5F8] text-gray-700 rounded-full transition-colors"
                >
                  {shortcut}
                </button>
              ))}
            </div>

            {/* Deep Dive Topics */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Deep Dive Topics</h4>
              <div className="flex flex-wrap gap-2">
                {[
                  'Phase 2 feasibility',
                  'Onboarding blockers',
                  'API integration',
                  'Customer feedback',
                ].map((topic) => (
                  <button
                    key={topic}
                    onClick={() => handleShortcutClick(topic)}
                    className="px-3 py-1 text-xs bg-[#F3E5F8] text-[#C9A0DC] rounded-full hover:bg-[#C9A0DC] hover:text-white transition-colors"
                  >
                    {topic}
                  </button>
                ))}
              </div>
            </div>

            {/* Chat Messages */}
            <div className="mb-4 max-h-64 overflow-y-auto space-y-3">
              {chatMessages.map((message, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-[#F3E5F8] text-gray-900 ml-8'
                      : 'bg-slate-100 text-gray-700 mr-8'
                  }`}
                >
                  <p className="text-sm">{message.content}</p>
                </div>
              ))}
              {isChatLoading && (
                <div className="p-3 bg-slate-100 rounded-lg mr-8">
                  <p className="text-sm text-gray-500">Thinking...</p>
                </div>
              )}
            </div>

            {/* Chat Input */}
            <div>
              <textarea
                placeholder="Ask anything about this meeting..."
                className="w-full p-3 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-[#C9A0DC] focus:border-transparent"
                rows={3}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
              />
              <button 
                onClick={handleSendMessage}
                disabled={isChatLoading || !chatInput.trim()}
                className="mt-2 w-full px-4 py-2 bg-[#C9A0DC] text-white rounded-md hover:bg-[#9B6DB8] transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Send className="w-4 h-4" />
                Ask
              </button>
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}
