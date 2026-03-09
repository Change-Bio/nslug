import { useEffect, useRef, useState } from 'react'
import { WHEPClient } from '../services/whep'
import './VideoFeed.css'

const VideoFeed = () => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const whepClientRef = useRef<WHEPClient | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [connecting, setConnecting] = useState(true)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const whepUrl = `${window.location.protocol}//${window.location.host}/camera/whep`

    const connect = async () => {
      try {
        setConnecting(true)
        setError(null)

        whepClientRef.current = new WHEPClient()
        await whepClientRef.current.connect(whepUrl, video)

        setConnecting(false)
      } catch (err) {
        console.error('WHEP connection failed:', err)
        setError(err instanceof Error ? err.message : 'Failed to connect')
        setConnecting(false)
      }
    }

    connect()

    return () => {
      if (whepClientRef.current) {
        whepClientRef.current.disconnect()
      }
    }
  }, [])

  return (
    <div className="video-feed-container">
      <h2>Live Camera Feed (WebRTC)</h2>
      <div className="video-wrapper">
        {connecting && <div className="video-status">Connecting...</div>}
        {error && <div className="video-status error">Error: {error}</div>}
        <video
          ref={videoRef}
          className="video-feed"
          controls
          autoPlay
          muted
          playsInline
        />
      </div>
    </div>
  )
}

export default VideoFeed
