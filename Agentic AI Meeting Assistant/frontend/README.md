# Agentic AI Meeting Assistant - Next.js Frontend

A modern, professional Next.js frontend for the Agentic AI Meeting Assistant, replacing the legacy HTML template with a clean, minimal design.

## Features

- **Multi-format meeting ingestion**: Text paste, file upload (.txt, .vtt, .srt), and audio/video upload
- **AI-powered extraction**: Automatic extraction of summaries, decisions, risks, and action items
- **Human-in-the-loop review**: Approve or reject individual action items with evidence
- **GitHub dispatch**: Create GitHub issues from approved items
- **Evidence-backed Q&A**: Ask questions about meeting transcripts
- **Professional minimal design**: Clean UI with minimal color palette

## Tech Stack

- **Framework**: Next.js 14.2.18 with TypeScript
- **Styling**: Tailwind CSS with custom minimal color palette
- **Icons**: Lucide React
- **Backend Integration**: FastAPI (existing Python backend)

## Setup Instructions

### Prerequisites

- Node.js 18+ installed
- Python backend running on `http://localhost:8000`
- Environment variables configured

### Installation

1. Navigate to the frontend directory:
```bash
cd "Agentic AI Meeting Assistant/frontend"
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables:
```bash
# Edit .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Running the Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Building for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with metadata
│   ├── page.tsx            # Main application page
│   └── globals.css         # Global styles with Tailwind
├── components/
│   ├── ui/                 # Reusable UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── textarea.tsx
│   │   └── badge.tsx
│   ├── UploadSection.tsx   # Meeting upload functionality
│   ├── ReviewSection.tsx   # Action item review interface
│   └── ResultsSection.tsx # Dispatch results and audit log
├── lib/
│   ├── api.ts              # API client functions
│   └── utils.ts            # Utility functions (cn helper)
├── public/                 # Static assets
└── package.json            # Dependencies
```

## Color Palette

The design uses a minimal professional color palette:

- **Background**: `#0A0A0A` (Near black)
- **Surface**: `#141414` (Dark gray)
- **Border**: `#262626` (Subtle gray)
- **Text Primary**: `#FAFAFA` (Near white)
- **Text Secondary**: `#A3A3A3` (Muted gray)
- **Primary**: `#3B82F6` (Professional blue)
- **Success**: `#10B981` (Green)
- **Error**: `#EF4444` (Red)
- **Warning**: `#F59E0B` (Amber)

## API Integration

The frontend communicates with the FastAPI backend through the `lib/api.ts` module. Key endpoints:

- `POST /ingest` - Text transcript ingestion
- `POST /ingest/file` - File upload
- `POST /media/direct-upload` - Media upload
- `POST /meetings/{id}/action-items/{id}/review` - Review action items
- `POST /meetings/{id}/dispatch` - Dispatch to GitHub
- `POST /meetings/{id}/ask` - Q&A about meetings
- `GET /meetings/{id}` - Get meeting details and audit log

## Development Notes

- The application uses Next.js App Router with TypeScript
- All components are client-side rendered ('use client')
- Tailwind CSS is configured with custom colors in `tailwind.config.ts`
- The API proxy is configured in `next.config.js` for development

## Migration from HTML Template

This Next.js application replaces the legacy `templates/ui.html` file with a modern, maintainable React-based frontend. All functionality from the HTML template has been preserved and enhanced with:

- Better component organization
- Type safety with TypeScript
- Improved state management
- Professional minimal design
- Better accessibility
- Easier maintenance and extensibility
