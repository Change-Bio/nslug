const API_BASE = '/api'

export interface PumpStatus {
  running: boolean
  mode: string | null
  turns_remaining: number
}

export async function getPumpStatus(): Promise<PumpStatus | null> {
  try {
    const response = await fetch(`${API_BASE}/pump/status`)
    return await response.json()
  } catch (error) {
    console.error('Failed to get pump status:', error)
    return null
  }
}

export async function movePump(turns: number, mode: 'forward' | 'backward'): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/pump/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ turns, mode })
    })
    return response.ok
  } catch (error) {
    console.error('Failed to move pump:', error)
    return false
  }
}

export async function stopPump(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/pump/stop`, {
      method: 'POST'
    })
    return response.ok
  } catch (error) {
    console.error('Failed to stop pump:', error)
    return false
  }
}
