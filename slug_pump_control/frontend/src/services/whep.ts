export class WHEPClient {
  private pc: RTCPeerConnection | null = null
  private videoElement: HTMLVideoElement | null = null

  async connect(whepUrl: string, videoElement: HTMLVideoElement) {
    this.videoElement = videoElement

    // Create peer connection
    this.pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    })

    // Handle incoming tracks
    this.pc.ontrack = (event) => {
      console.log('WebRTC track received:', event.track.kind, event.streams.length)
      if (!videoElement.srcObject && event.streams.length > 0) {
        console.log('Setting video srcObject')
        videoElement.srcObject = event.streams[0]
      }
    }

    // Debug connection state
    this.pc.onconnectionstatechange = () => {
      console.log('WebRTC connection state:', this.pc?.connectionState)
    }

    this.pc.oniceconnectionstatechange = () => {
      console.log('ICE connection state:', this.pc?.iceConnectionState)
    }

    // Add transceiver for receiving video only (no audio in camera stream)
    this.pc.addTransceiver('video', { direction: 'recvonly' })

    // Create offer
    const offer = await this.pc.createOffer()
    await this.pc.setLocalDescription(offer)

    // Send offer to WHEP endpoint
    const response = await fetch(whepUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/sdp'
      },
      body: offer.sdp
    })

    if (!response.ok) {
      throw new Error(`WHEP request failed: ${response.status}`)
    }

    // Get answer from server
    const answerSdp = await response.text()
    await this.pc.setRemoteDescription({
      type: 'answer',
      sdp: answerSdp
    })
  }

  disconnect() {
    if (this.pc) {
      this.pc.close()
      this.pc = null
    }
    if (this.videoElement) {
      this.videoElement.srcObject = null
    }
  }
}
