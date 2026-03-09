import { useState, useEffect } from 'react'
import VideoFeed from './components/VideoFeed'
import PumpControls from './components/PumpControls'
import { getPumpStatus, PumpStatus } from './services/api'
import './App.css'

function App() {
  const [pumpStatus, setPumpStatus] = useState<PumpStatus>({
    running: false,
    mode: null,
    turns_remaining: 0
  })

  useEffect(() => {
    const interval = setInterval(async () => {
      const status = await getPumpStatus()
      if (status) setPumpStatus(status)
    }, 500)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <h1>🐌 Slug Pump Control</h1>
      </header>

      <main className="app-main">
        <VideoFeed />
        <PumpControls pumpStatus={pumpStatus} />
      </main>
    </div>
  )
}

export default App
