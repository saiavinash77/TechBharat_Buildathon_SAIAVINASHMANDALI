'use client'

import { ArrowRight, Upload, Mic, FileText, Github, CheckCircle, Shield, Lock, Users, Play } from 'lucide-react'
import { Button } from './ui/button'
import Link from 'next/link'

interface LandingPageProps {
  onComplete: () => void
}

export function LandingPage({ onComplete }: LandingPageProps) {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 bg-white/90 backdrop-blur-md border-b border-gray-200 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-xl font-semibold text-gray-900">NOVA</h1>
          <div className="flex gap-4">
            <Link href="/join">
              <Button variant="outline" size="sm" className="border-gray-300 text-gray-700">
                Join Team
              </Button>
            </Link>
            <Button size="sm" onClick={onComplete} className="bg-[#C9A0DC] hover:bg-[#9B6DB8] text-white">
              Get Started
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 bg-gradient-to-b from-[#F3E5F8] to-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
                NOVA
              </h2>
              <p className="text-3xl text-[#C9A0DC] font-semibold mb-6">
                Your Meeting Intelligence
              </p>
              <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                Automatically capture AI meeting notes and action items. Turn your meetings into actionable tasks with human-level accuracy.
              </p>
              <div className="flex gap-4">
                <Button size="default" onClick={onComplete} className="bg-[#C9A0DC] hover:bg-[#9B6DB8] text-white rounded-md px-6 py-3">
                  <span>Start Free</span>
                  <ArrowRight className="ml-2 w-4 h-4" />
                </Button>
                <Link href="/join">
                  <Button size="default" variant="outline" className="border-gray-300 text-gray-700 rounded-md px-6 py-3">
                    Join Team
                  </Button>
                </Link>
              </div>
            </div>
            <div className="relative">
              <div className="bg-gradient-to-br from-[#C9A0DC] to-[#9B6DB8] rounded-3xl p-8 shadow-2xl">
                <div className="bg-white rounded-2xl overflow-hidden">
                  <video 
                    src="/video.mp4" 
                    autoPlay 
                    loop 
                    muted
                    controls
                    playsInline
                    className="w-full h-auto"
                    disablePictureInPicture
                  />
                  <div className="p-6">
                    <div className="flex items-center gap-4 mb-4">
                      <div className="w-12 h-12 rounded-full bg-[#F3E5F8] flex items-center justify-center">
                        <Play className="w-6 h-6 text-[#C9A0DC]" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">Team Standup</p>
                        <p className="text-sm text-gray-500">Today at 10:00 AM</p>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        <span className="text-sm text-gray-700">API documentation by Friday</span>
                      </div>
                      <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg">
                        <CheckCircle className="w-5 h-5 text-yellow-600" />
                        <span className="text-sm text-gray-700">Database migration review</span>
                      </div>
                      <div className="flex items-center gap-3 p-3 bg-[#F3E5F8] rounded-lg">
                        <Github className="w-5 h-5 text-[#C9A0DC]" />
                        <span className="text-sm text-gray-700">CI/CD pipeline setup</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Turn Meetings into Action
            </h2>
            <p className="text-xl text-gray-600">
              All your recordings and recaps in one place
            </p>
          </div>

          <div className="space-y-20">
            {[
              {
                icon: <Mic className="w-8 h-8" />,
                title: "AI Transcription",
                description: "Groq Whisper-powered transcription with timestamps and speaker identification",
                reverse: false
              },
              {
                icon: <FileText className="w-8 h-8" />,
                title: "Action Extraction",
                description: "3-tier confidence system for automatic action item detection",
                reverse: true
              },
              {
                icon: <Github className="w-8 h-8" />,
                title: "GitHub Sync",
                description: "Auto-create issues and assign tasks directly to your repositories",
                reverse: false
              },
              {
                icon: <Users className="w-8 h-8" />,
                title: "Team Mapping",
                description: "Connect team emails to GitHub handles for seamless assignment",
                reverse: true
              }
            ].map((feature, idx) => (
              <div
                key={idx}
                className={`grid md:grid-cols-2 gap-12 items-center ${feature.reverse ? 'md:flex-row-reverse' : ''}`}
              >
                <div>
                  <div className="w-16 h-16 rounded-xl bg-[#F3E5F8] flex items-center justify-center mb-6">
                    <span className="text-[#C9A0DC]">{feature.icon}</span>
                  </div>
                  <h3 className="text-3xl font-bold text-gray-900 mb-4">{feature.title}</h3>
                  <p className="text-xl text-gray-600 leading-relaxed">{feature.description}</p>
                </div>
                <div className="bg-gradient-to-br from-[#C9A0DC] to-[#9B6DB8] rounded-2xl p-8 shadow-lg">
                  {feature.title === "AI Transcription" ? (
                    <img 
                      src="/transcription-feature.jpg" 
                      alt="AI Transcription Feature" 
                      className="w-full h-auto rounded-xl"
                    />
                  ) : feature.title === "Action Extraction" ? (
                    <img 
                      src="/action-extraction-feature.jpg" 
                      alt="Action Extraction Feature" 
                      className="w-full h-auto rounded-xl"
                    />
                  ) : feature.title === "GitHub Sync" ? (
                    <img 
                      src="/github-sync-feature.jpg" 
                      alt="GitHub Sync Feature" 
                      className="w-full h-auto rounded-xl"
                    />
                  ) : feature.title === "Team Mapping" ? (
                    <img 
                      src="/team-mapping-feature.jpg" 
                      alt="Team Mapping Feature" 
                      className="w-full h-auto rounded-xl"
                    />
                  ) : (
                    <div className="bg-white rounded-xl p-6">
                      <div className="flex items-center gap-4 mb-4">
                        <div className="w-10 h-10 rounded-full bg-[#F3E5F8] flex items-center justify-center">
                          <span className="text-[#C9A0DC]">{feature.icon}</span>
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900">Sample Meeting</p>
                          <p className="text-sm text-gray-500">Today at 10:00 AM</p>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div className="flex items-center gap-3 p-3 bg-[#F3E5F8] rounded-lg">
                          <CheckCircle className="w-5 h-5 text-[#C9A0DC]" />
                          <span className="text-sm text-gray-700">Action item detected</span>
                        </div>
                        <div className="flex items-center gap-3 p-3 bg-[#F3E5F8] rounded-lg">
                          <CheckCircle className="w-5 h-5 text-[#C9A0DC]" />
                          <span className="text-sm text-gray-700">Task assigned</span>
                        </div>
                        <div className="flex items-center gap-3 p-3 bg-[#F3E5F8] rounded-lg">
                          <CheckCircle className="w-5 h-5 text-[#C9A0DC]" />
                          <span className="text-sm text-gray-700">GitHub issue created</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Get more from your meeting notes
          </h2>
          <p className="text-xl text-gray-600 mb-12">
            Start turning them into action today
          </p>

          <Button size="lg" onClick={onComplete} className="bg-[#C9A0DC] hover:bg-[#9B6DB8] text-white text-lg px-12 py-6">
            <span>Start Free</span>
            <ArrowRight className="ml-2 w-5 h-5" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 bg-gray-50 border-t border-gray-200">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-gray-600">
            © 2024 NOVA. Your Meeting Intelligence. Built for TechBharat Buildathon.
          </p>
        </div>
      </footer>
    </div>
  )
}
