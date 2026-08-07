'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Github, User, Mail, CheckCircle } from 'lucide-react'

export default function JoinPage() {
  const [formData, setFormData] = useState({
    inviteToken: '',
    email: '',
    fullName: '',
    githubHandle: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setSubmitStatus('idle')
    setErrorMessage('')

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${API_URL}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          invite_token: formData.inviteToken,
          email: formData.email,
          full_name: formData.fullName,
          github_handle: formData.githubHandle.replace('@', '')
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to join team')
      }

      setSubmitStatus('success')
      setFormData({ inviteToken: '', email: '', fullName: '', githubHandle: '' })
    } catch (error) {
      setSubmitStatus('error')
      setErrorMessage(error instanceof Error ? error.message : 'An error occurred')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
              <Github className="w-8 h-8 text-primary" />
            </div>
          </div>
          <CardTitle className="text-2xl">Join Your Team</CardTitle>
          <CardDescription>
            Connect your email to your GitHub handle for automatic task assignment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="inviteToken" className="block text-sm font-medium text-text-primary mb-2">
                Invite Token
              </label>
              <Input
                id="inviteToken"
                name="inviteToken"
                type="text"
                placeholder="Enter your invite token"
                value={formData.inviteToken}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-text-primary mb-2">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4" />
                  Teammate Email
                </div>
              </label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="you@company.com"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-text-primary mb-2">
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4" />
                  Full Name
                </div>
              </label>
              <Input
                id="fullName"
                name="fullName"
                type="text"
                placeholder="John Doe"
                value={formData.fullName}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <label htmlFor="githubHandle" className="block text-sm font-medium text-text-primary mb-2">
                <div className="flex items-center gap-2">
                  <Github className="w-4 h-4" />
                  GitHub Handle
                </div>
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary">@</span>
                <Input
                  id="githubHandle"
                  name="githubHandle"
                  type="text"
                  placeholder="username"
                  value={formData.githubHandle}
                  onChange={handleChange}
                  className="pl-7"
                  required
                />
              </div>
              <p className="text-xs text-text-secondary mt-1">
                This will be used to assign GitHub issues to you
              </p>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Joining...' : 'Join Team'}
            </Button>

            {submitStatus === 'success' && (
              <div className="flex items-center gap-2 p-3 bg-success/10 border border-success/30 rounded-lg">
                <CheckCircle className="w-5 h-5 text-success" />
                <span className="text-sm text-success">
                  Successfully joined! Your GitHub handle is now mapped.
                </span>
              </div>
            )}

            {submitStatus === 'error' && (
              <div className="p-3 bg-error/10 border border-error/30 rounded-lg">
                <p className="text-sm text-error">{errorMessage}</p>
              </div>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
