'use client'

import { useState } from 'react'
import { Check, X, ChevronDown, ChevronUp, Clock, User } from 'lucide-react'
import { Button } from './ui/button'
import { Badge } from './ui/badge'

interface ActionItem {
  id: string
  title: string
  classification: 'EXPLICIT_COMMITMENT' | 'NEEDS_CONFIRMATION' | 'DISCUSSION_ONLY'
  quote_provenance: string
  speaker_name: string
  confidence_score?: number
  review_status?: 'APPROVED' | 'REJECTED' | 'PENDING'
  proposed_owner_name?: string
  due_date?: string
}

interface ReviewCardsProps {
  items: ActionItem[]
  onApprove: (itemId: string) => void
  onReject: (itemId: string) => void
  onDispatch: () => void
}

export function ReviewCards({ items, onApprove, onReject, onDispatch }: ReviewCardsProps) {
  const [activeTab, setActiveTab] = useState<'all' | 'explicit' | 'needs_confirm' | 'discussion'>('all')
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())

  const toggleExpand = (itemId: string) => {
    const newExpanded = new Set(expandedItems)
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId)
    } else {
      newExpanded.add(itemId)
    }
    setExpandedItems(newExpanded)
  }

  const filteredItems = items.filter(item => {
    if (activeTab === 'all') return item.classification !== 'DISCUSSION_ONLY'
    if (activeTab === 'explicit') return item.classification === 'EXPLICIT_COMMITMENT'
    if (activeTab === 'needs_confirm') return item.classification === 'NEEDS_CONFIRMATION'
    if (activeTab === 'discussion') return item.classification === 'DISCUSSION_ONLY'
    return true
  })

  const approvedCount = items.filter(i => i.review_status === 'APPROVED').length

  const getClassificationBadge = (classification: string) => {
    switch (classification) {
      case 'EXPLICIT_COMMITMENT':
        return <Badge variant="success">EXPLICIT_COMMITMENT</Badge>
      case 'NEEDS_CONFIRMATION':
        return <Badge variant="warning">NEEDS_CONFIRMATION</Badge>
      case 'DISCUSSION_ONLY':
        return <Badge variant="secondary">DISCUSSION_ONLY</Badge>
      default:
        return <Badge variant="default">{classification}</Badge>
    }
  }

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-border pb-4">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'all'
              ? 'bg-primary text-white'
              : 'bg-background text-text-secondary hover:bg-primary-light'
          }`}
        >
          All ({items.filter(i => i.classification !== 'DISCUSSION_ONLY').length})
        </button>
        <button
          onClick={() => setActiveTab('explicit')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'explicit'
              ? 'bg-primary text-white'
              : 'bg-background text-text-secondary hover:bg-primary-light'
          }`}
        >
          Explicit ({items.filter(i => i.classification === 'EXPLICIT_COMMITMENT').length})
        </button>
        <button
          onClick={() => setActiveTab('needs_confirm')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'needs_confirm'
              ? 'bg-primary text-white'
              : 'bg-background text-text-secondary hover:bg-primary-light'
          }`}
        >
          Needs Review ({items.filter(i => i.classification === 'NEEDS_CONFIRMATION').length})
        </button>
        <button
          onClick={() => setActiveTab('discussion')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'discussion'
              ? 'bg-primary text-white'
              : 'bg-background text-text-secondary hover:bg-primary-light'
          }`}
        >
          Discussion ({items.filter(i => i.classification === 'DISCUSSION_ONLY').length})
        </button>
      </div>

      {/* Action Items */}
      <div className="space-y-4">
        {filteredItems.map((item) => (
          <div
            key={item.id}
            className={`bg-surface border rounded-xl p-6 transition-all ${
              item.review_status === 'APPROVED' ? 'border-success/50 bg-success/5' :
              item.review_status === 'REJECTED' ? 'border-error/50 bg-error/5' :
              'border-border'
            }`}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="font-semibold text-text-primary text-lg">{item.title}</h3>
                  {getClassificationBadge(item.classification)}
                </div>
                
                <div className="flex items-center gap-4 text-sm text-text-secondary">
                  <div className="flex items-center gap-1">
                    <User className="w-4 h-4" />
                    <span>{item.speaker_name}</span>
                  </div>
                  {item.due_date && (
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <span>{item.due_date}</span>
                    </div>
                  )}
                  {item.confidence_score && (
                    <span>Confidence: {Math.round(item.confidence_score * 100)}%</span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                {item.classification !== 'DISCUSSION_ONLY' && (
                  <>
                    <Button
                      variant={item.review_status === 'APPROVED' ? 'success' : 'outline'}
                      size="sm"
                      onClick={() => onApprove(item.id)}
                    >
                      <Check className="w-4 h-4 mr-1" />
                      Approve
                    </Button>
                    <Button
                      variant={item.review_status === 'REJECTED' ? 'error' : 'outline'}
                      size="sm"
                      onClick={() => onReject(item.id)}
                    >
                      <X className="w-4 h-4 mr-1" />
                      Reject
                    </Button>
                  </>
                )}
              </div>
            </div>

            {/* Evidence Quote Accordion */}
            <div className="border-t border-border pt-4">
              <button
                onClick={() => toggleExpand(item.id)}
                className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
              >
                {expandedItems.has(item.id) ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
                <span>Evidence Quote</span>
              </button>
              
              {expandedItems.has(item.id) && (
                <div className="mt-3 p-4 bg-background rounded-lg">
                  <p className="text-sm text-text-primary italic">"{item.quote_provenance}"</p>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-xs text-text-secondary">Timestamp: {item.due_date || 'N/A'}</span>
                    <button
                      className="text-xs text-primary hover:underline"
                      onClick={() => {
                        // TODO: Seek video to timestamp
                        console.log('Seek to timestamp:', item.due_date)
                      }}
                    >
                      Jump to video
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Dispatch Button */}
      {approvedCount > 0 && (
        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
          <Button
            size="lg"
            onClick={onDispatch}
            className="shadow-xl"
          >
            Approve & Sync {approvedCount} Selected to GitHub
          </Button>
        </div>
      )}

      {filteredItems.length === 0 && (
        <div className="text-center py-12 text-text-secondary">
          <p>No action items in this category.</p>
        </div>
      )}
    </div>
  )
}
