'use client'

import { useState } from 'react'
import { LandingPage } from '@/components/LandingPage'
import { MeetingInterface } from '@/components/MeetingInterface'
import { Signup } from '@/components/Signup'
import { IndividualDashboard } from '@/components/IndividualDashboard'
import { OrganizationDashboard } from '@/components/OrganizationDashboard'

type FlowState = 'landing' | 'signup' | 'individual-dashboard' | 'organization-dashboard' | 'meeting-interface'

export default function Home() {
  const [flowState, setFlowState] = useState<FlowState>('landing')
  const [userData, setUserData] = useState<{ email: string; name: string } | null>(null)
  const [accountType, setAccountType] = useState<'individual' | 'organization' | null>(null)
  const [videoData, setVideoData] = useState<{ file: File; url: string } | null>(null)

  const handleLandingComplete = () => {
    setFlowState('signup')
  }

  const handleBackToLanding = () => {
    setFlowState('landing')
  }

  const handleSignupComplete = (data: { email: string; name: string }, type: 'individual' | 'organization') => {
    setUserData(data)
    setAccountType(type)
    if (type === 'individual') {
      setFlowState('individual-dashboard')
    } else {
      setFlowState('organization-dashboard')
    }
  }

  const handleVideoUploaded = (data: { file: File; url: string; meetingId: string; reviewData: any }) => {
    setVideoData({ file: data.file, url: data.url })
    setFlowState('meeting-interface')
  }

  const handleBackToSignup = () => {
    setFlowState('signup')
  }

  const handleJoinOrganization = () => {
    // TODO: Implement join organization flow
    setFlowState('meeting-interface')
  }

  const handleCreateOrganization = () => {
    // TODO: Implement create organization flow
    setFlowState('meeting-interface')
  }

  if (flowState === 'landing') {
    return <LandingPage onComplete={handleLandingComplete} />
  }

  if (flowState === 'signup') {
    return <Signup onSignupComplete={handleSignupComplete} onBack={handleBackToLanding} />
  }

  if (flowState === 'individual-dashboard') {
    return <IndividualDashboard onVideoUploaded={handleVideoUploaded} onBack={handleBackToSignup} />
  }

  if (flowState === 'organization-dashboard') {
    return <OrganizationDashboard 
      onJoinOrganization={handleJoinOrganization}
      onCreateOrganization={handleCreateOrganization}
    />
  }

  return <MeetingInterface videoData={videoData} />
}
