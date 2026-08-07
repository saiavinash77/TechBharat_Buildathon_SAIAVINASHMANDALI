'use client'

import { useState } from 'react'
import { Plus, MessageSquare, Heart, Share2, MoreVertical } from 'lucide-react'
import { Button } from './ui/button'

interface MeetingSectionProps {
  title: string
  items: { id: string; content: string; author?: string; tags?: string[] }[]
  onAddItem?: (content: string) => void
  color?: 'purple' | 'green' | 'orange'
}

export function MeetingSection({ title, items, onAddItem, color = 'purple' }: MeetingSectionProps) {
  const [isAdding, setIsAdding] = useState(false)
  const [newItem, setNewItem] = useState('')

  const colorStyles = {
    purple: 'border-[#C9A0DC] bg-[#F3E5F8]',
    green: 'border-green-200 bg-green-50/50',
    orange: 'border-orange-200 bg-orange-50/50',
  }

  const handleAdd = () => {
    if (newItem.trim() && onAddItem) {
      onAddItem(newItem)
      setNewItem('')
      setIsAdding(false)
    }
  }

  return (
    <div className={`border rounded-2xl p-6 ${colorStyles[color]}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-text-primary text-lg">{title}</h3>
        <Button variant="ghost" size="icon" onClick={() => setIsAdding(true)}>
          <Plus className="w-5 h-5" />
        </Button>
      </div>

      {isAdding && (
        <div className="mb-4 animate-in fade-in slide-in-from-top-2">
          <textarea
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            placeholder={`Add to ${title}...`}
            className="w-full p-3 border border-border rounded-xl bg-surface text-text-primary text-sm resize-none focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            rows={3}
          />
          <div className="flex justify-end gap-2 mt-2">
            <Button variant="outline" size="sm" onClick={() => setIsAdding(false)}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleAdd}>
              Add
            </Button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {items.map((item) => (
          <div
            key={item.id}
            className="bg-surface border border-border rounded-xl p-4 hover:shadow-md transition-shadow"
          >
            <p className="text-text-primary text-sm mb-3">{item.content}</p>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {item.author && (
                  <span className="px-2 py-1 bg-primary/10 text-primary text-xs font-medium rounded-full">
                    {item.author}
                  </span>
                )}
                {item.tags?.map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-background text-text-secondary text-xs rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MessageSquare className="w-4 h-4 text-text-secondary" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Heart className="w-4 h-4 text-text-secondary" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Share2 className="w-4 h-4 text-text-secondary" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreVertical className="w-4 h-4 text-text-secondary" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {items.length === 0 && !isAdding && (
        <div className="text-center py-8 text-text-secondary text-sm">
          No items yet. Click + to add one.
        </div>
      )}
    </div>
  )
}
