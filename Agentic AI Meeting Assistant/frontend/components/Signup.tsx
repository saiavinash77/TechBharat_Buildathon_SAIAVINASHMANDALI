'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ArrowLeft } from 'lucide-react'

interface SignupProps {
  onSignupComplete: (userData: { email: string; name: string }, type: 'individual' | 'organization') => void
  onBack: () => void
}

export function Signup({ onSignupComplete, onBack }: SignupProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [accountType, setAccountType] = useState<'individual' | 'organization'>('individual')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      // For demo purposes, immediately complete signup
      // The backend uses server-side InsForge API key, not user auth
      onSignupComplete({ email, name }, accountType)
      setLoading(false)
    } catch (error) {
      setLoading(false)
      setError('Signup failed. Please try again.')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#F3E5F8] to-white flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <button
          onClick={onBack}
          className="mb-4 flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">NOVA</h1>
            <p className="text-[#C9A0DC] font-semibold">Your Meeting Intelligence</p>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Create Account
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="mt-1"
              />
            </div>

            <div>
              <Label>Account Type</Label>
              <div className="mt-2 grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setAccountType('individual')}
                  className={`p-4 rounded-lg border-2 text-left transition-colors ${
                    accountType === 'individual'
                      ? 'border-[#C9A0DC] bg-[#F3E5F8]'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-semibold text-gray-900">Individual</div>
                  <div className="text-sm text-gray-600">Personal use</div>
                </button>
                <button
                  type="button"
                  onClick={() => setAccountType('organization')}
                  className={`p-4 rounded-lg border-2 text-left transition-colors ${
                    accountType === 'organization'
                      ? 'border-[#C9A0DC] bg-[#F3E5F8]'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-semibold text-gray-900">Organization</div>
                  <div className="text-sm text-gray-600">Team collaboration</div>
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full bg-[#C9A0DC] hover:bg-[#9B6DB8] text-white rounded-md"
              disabled={loading}
            >
              {loading ? 'Creating Account...' : 'Sign Up'}
            </Button>
          </form>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="mt-6 text-center">
            <button
              type="button"
              className="text-[#C9A0DC] hover:text-[#9B6DB8] font-medium"
            >
              Already have an account? Sign in
            </button>
          </div>
        </div>

        <p className="text-center text-gray-500 text-sm mt-6">
          By continuing, you agree to NOVA's Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  )
}
