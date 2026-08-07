'use client'

import { Button } from '@/components/ui/button'
import { Building2, Plus } from 'lucide-react'

interface OrganizationDashboardProps {
  onJoinOrganization: () => void
  onCreateOrganization: () => void
}

export function OrganizationDashboard({ onJoinOrganization, onCreateOrganization }: OrganizationDashboardProps) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#F3E5F8] to-white flex items-center justify-center px-4">
      <div className="max-w-2xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">NOVA</h1>
          <p className="text-[#C9A0DC] font-semibold">Your Meeting Intelligence</p>
        </div>

        <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
          Organization Setup
        </h2>

        <div className="grid md:grid-cols-2 gap-6">
          <button
            onClick={onJoinOrganization}
            className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition-shadow text-left border-2 border-transparent hover:border-[#C9A0DC]"
          >
            <div className="w-16 h-16 rounded-xl bg-[#F3E5F8] flex items-center justify-center mb-4">
              <Building2 className="w-8 h-8 text-[#C9A0DC]" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Join Organization</h3>
            <p className="text-gray-600">
              Enter an organization code to join an existing team and start collaborating.
            </p>
          </button>

          <button
            onClick={onCreateOrganization}
            className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition-shadow text-left border-2 border-transparent hover:border-[#C9A0DC]"
          >
            <div className="w-16 h-16 rounded-xl bg-[#F3E5F8] flex items-center justify-center mb-4">
              <Plus className="w-8 h-8 text-[#C9A0DC]" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Create Organization</h3>
            <p className="text-gray-600">
              Start a new organization and invite team members to collaborate on meetings.
            </p>
          </button>
        </div>
      </div>
    </div>
  )
}
