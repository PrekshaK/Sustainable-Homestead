import { useState, useEffect } from 'react'
import { simulateFull } from './api'
import { DEFAULT_INPUTS, buildRequest } from './defaults'
import { ScenarioPanel } from './ScenarioPanel'
import { Dashboard } from './Dashboard'

function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(t)
  }, [value, delay])
  return debounced
}

export default function App() {
  const [inputs, setInputs] = useState(DEFAULT_INPUTS)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const debouncedInputs = useDebounce(inputs, 350)

  useEffect(() => {
    setLoading(true)
    setError(null)
    simulateFull(buildRequest(debouncedInputs))
      .then(data => { setResult(data); setLoading(false) })
      .catch(err => { setError(err.message); setLoading(false) })
  }, [debouncedInputs])

  function setInput(section, key, value) {
    setInputs(prev => ({
      ...prev,
      [section]: { ...prev[section], [key]: value },
    }))
  }

  function setCropField(index, key, value) {
    setInputs(prev => ({
      ...prev,
      crops: prev.crops.map((c, i) => i === index ? { ...c, [key]: value } : c),
    }))
  }

  function addCrop() {
    setInputs(prev => ({
      ...prev,
      crops: [...prev.crops, { crop: 'corn', land_acres: 1, days_in_season: 60 }],
    }))
  }

  function removeCrop(index) {
    setInputs(prev => ({
      ...prev,
      crops: prev.crops.filter((_, i) => i !== index),
    }))
  }

  function setCattleField(index, key, value) {
    setInputs(prev => ({
      ...prev,
      cattle: prev.cattle.map((c, i) => i === index ? { ...c, [key]: value } : c),
    }))
  }

  function addCattle() {
    setInputs(prev => ({
      ...prev,
      cattle: [...prev.cattle, { animal: 'chicken', count: 5 }],
    }))
  }

  function removeCattle(index) {
    setInputs(prev => ({
      ...prev,
      cattle: prev.cattle.filter((_, i) => i !== index),
    }))
  }

  return (
    <div className="flex h-screen bg-gray-950 text-white overflow-hidden">
      <aside className="w-72 flex-shrink-0 overflow-y-auto border-r border-gray-800 p-5">
        <ScenarioPanel inputs={inputs} setInput={setInput}
          setCropField={setCropField} addCrop={addCrop} removeCrop={removeCrop}
          setCattleField={setCattleField} addCattle={addCattle} removeCattle={removeCattle} />
      </aside>
      <main className="flex-1 overflow-y-auto p-6">
        <Dashboard result={result} loading={loading} error={error} />
      </main>
    </div>
  )
}
