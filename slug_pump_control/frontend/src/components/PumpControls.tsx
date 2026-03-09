import { useState } from 'react'
import { movePump, stopPump, PumpStatus } from '../services/api'
import './PumpControls.css'

interface PumpControlsProps {
  pumpStatus: PumpStatus
}

const PumpControls = ({ pumpStatus }: PumpControlsProps) => {
  const [turns, setTurns] = useState(1)
  const [message, setMessage] = useState('')

  const handleMove = async (mode: 'forward' | 'backward') => {
    if (turns <= 0) {
      setMessage('Error: Turns must be greater than 0')
      return
    }

    const success = await movePump(turns, mode)
    if (success) {
      setMessage(`Pump moving ${mode} for ${turns} turns...`)
    } else {
      setMessage('Error: Failed to start pump')
    }
  }

  const handleStop = async () => {
    const success = await stopPump()
    if (success) {
      setMessage('Pump stopped')
    } else {
      setMessage('Error: Failed to stop pump')
    }
  }

  return (
    <div className="pump-controls-container">
      <h2>Pump Controls</h2>

      <div className="status-display">
        <div className="status-item">
          <span className="label">Status:</span>
          <span className={`value ${pumpStatus.running ? 'running' : ''}`}>
            {pumpStatus.running ? 'Running' : 'Stopped'}
          </span>
        </div>
        {pumpStatus.running && (
          <>
            <div className="status-item">
              <span className="label">Mode:</span>
              <span className="value">{pumpStatus.mode}</span>
            </div>
            <div className="status-item">
              <span className="label">Turns Remaining:</span>
              <span className="value">{pumpStatus.turns_remaining.toFixed(2)}</span>
            </div>
          </>
        )}
      </div>

      <div className="controls">
        <div className="input-group">
          <label htmlFor="turns">Number of Turns:</label>
          <input
            id="turns"
            type="number"
            value={turns}
            onChange={(e) => setTurns(parseFloat(e.target.value))}
            step="0.1"
            min="0"
            disabled={pumpStatus.running}
          />
        </div>

        <div className="button-group">
          <button
            className="btn btn-forward"
            onClick={() => handleMove('forward')}
            disabled={pumpStatus.running}
          >
            ⬆️ Forward
          </button>
          <button
            className="btn btn-backward"
            onClick={() => handleMove('backward')}
            disabled={pumpStatus.running}
          >
            ⬇️ Backward
          </button>
          <button
            className="btn btn-stop"
            onClick={handleStop}
            disabled={!pumpStatus.running}
          >
            ⏹️ Stop
          </button>
        </div>
      </div>

      {message && (
        <div className={`message ${message.includes('Error') ? 'error' : 'info'}`}>
          {message}
        </div>
      )}
    </div>
  )
}

export default PumpControls
