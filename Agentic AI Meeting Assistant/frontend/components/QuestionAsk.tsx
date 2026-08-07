'use client'

import { useState } from 'react'
import { Send, Loader2, Sparkles } from 'lucide-react'
import { Button } from './ui/button'
import { Input } from './ui/input'

interface QuestionAskProps {
  onAskQuestion: (question: string) => Promise<string>
}

export function QuestionAsk({ onAskQuestion }: QuestionAskProps) {
  const [question, setQuestion] = useState('')
  const [isAsking, setIsAsking] = useState(false)
  const [answer, setAnswer] = useState('')
  const [history, setHistory] = useState<{ question: string; answer: string }[]>([])

  const handleAsk = async () => {
    if (!question.trim() || isAsking) return

    setIsAsking(true)
    setAnswer('')

    try {
      const response = await onAskQuestion(question)
      setAnswer(response)
      setHistory(prev => [...prev, { question, answer: response }])
      setQuestion('')
    } catch (error) {
      setAnswer('Sorry, I encountered an error. Please try again.')
    } finally {
      setIsAsking(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAsk()
    }
  }

  return (
    <div className="bg-surface border border-border rounded-2xl p-6">
      <div className="flex items-center gap-2 mb-6">
        <Sparkles className="w-5 h-5 text-primary" />
        <h3 className="font-semibold text-text-primary">Ask about this meeting</h3>
      </div>

      {/* Question Input */}
      <div className="flex gap-3 mb-6">
        <Input
          placeholder="Ask anything about the meeting..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isAsking}
          className="flex-1"
        />
        <Button onClick={handleAsk} disabled={isAsking || !question.trim()}>
          {isAsking ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </Button>
      </div>

      {/* Current Answer */}
      {answer && (
        <div className="bg-primary-light border border-primary/20 rounded-xl p-4 mb-6 animate-in fade-in slide-in-from-bottom-2">
          <p className="text-text-primary text-sm leading-relaxed">{answer}</p>
        </div>
      )}

      {/* Question History */}
      {history.length > 0 && (
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-text-secondary">Previous questions</h4>
          {history.slice().reverse().map((item, idx) => (
            <div
              key={idx}
              className="bg-background border border-border rounded-xl p-4"
            >
              <p className="text-sm font-medium text-text-primary mb-2">{item.question}</p>
              <p className="text-sm text-text-secondary">{item.answer}</p>
            </div>
          ))}
        </div>
      )}

      {/* Quick Questions */}
      <div className="mt-6 pt-6 border-t border-border">
        <h4 className="text-sm font-medium text-text-secondary mb-3">Quick questions</h4>
        <div className="flex flex-wrap gap-2">
          {[
            'What were the key decisions?',
            'Who committed to what?',
            'What are the action items?',
            'What risks were mentioned?'
          ].map((quickQuestion, idx) => (
            <button
              key={idx}
              onClick={() => setQuestion(quickQuestion)}
              className="px-3 py-1.5 bg-background border border-border rounded-full text-sm text-text-secondary hover:border-primary hover:text-primary transition-colors"
            >
              {quickQuestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
