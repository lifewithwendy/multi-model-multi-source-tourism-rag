import { useState } from 'react'
import './App.css'
import Header from './components/Header'
import ModeSelector from './components/ModeSelector'
import StructuredFilters from './components/StructuredFilters'
import ImageFilters from './components/ImageFilters'
import Presets from './components/Presets'
import ResultsView from './components/ResultsView'

function App() {
  const [queryMode, setQueryMode] = useState('hybrid') // hybrid | structured | semantic | image
  const [query, setQuery] = useState('')
  const [file, setFile] = useState(null)
  const [topK, setTopK] = useState(3)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [response, setResponse] = useState(null)
  const [activeTab, setActiveTab] = useState('semantic') // semantic | structured | image (for raw results view)

  // Structured query filters
  const [categoryFilter, setCategoryFilter] = useState('')
  const [districtFilter, setDistrictFilter] = useState('')
  const [maxFeeFilter, setMaxFeeFilter] = useState('')
  const [difficultyFilter, setDifficultyFilter] = useState('')

  // Image mode parameters
  const [textQueryFilter, setTextQueryFilter] = useState('')

  const presets = [
    {
      label: "Waterfalls in Kandy (Structured)",
      mode: "structured",
      query: "Show me moderate difficulty waterfalls in Kandy",
      filters: { category: "Waterfall", district: "Kandy", difficulty: "Moderate", maxFee: "" }
    },
    {
      label: "Safe Swimming in Galle (Hybrid)",
      mode: "hybrid",
      query: "Show me photos of beaches in Galle that are safe for swimming."
    },
    {
      label: "Turtles & Sunset (Semantic)",
      mode: "semantic",
      query: "Where is a good place to see turtles and enjoy a quiet sunset?"
    }
  ]

  const handlePresetClick = (preset) => {
    setQueryMode(preset.mode)
    setQuery(preset.query)
    setFile(null)
    if (preset.filters) {
      setCategoryFilter(preset.filters.category || '')
      setDistrictFilter(preset.filters.district || '')
      setDifficultyFilter(preset.filters.difficulty || '')
      setMaxFeeFilter(preset.filters.maxFee || '')
    } else {
      setCategoryFilter('')
      setDistrictFilter('')
      setDifficultyFilter('')
      setMaxFeeFilter('')
    }
    setTextQueryFilter('')
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleClearFile = () => {
    setFile(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    // Validation
    if (queryMode === 'structured') {
      if (!categoryFilter && !districtFilter && !maxFeeFilter && !difficultyFilter && !query.trim()) {
        setError('Please specify at least one filter or a query question.')
        return;
      }
    } else if (queryMode === 'semantic') {
      if (!query.trim()) {
        setError('Please enter a semantic search query.')
        return;
      }
    } else if (queryMode === 'image') {
      if (!file && !textQueryFilter.trim()) {
        setError('Please upload an image or provide a descriptive visual query.')
        return;
      }
    } else if (queryMode === 'hybrid') {
      if (!query.trim() && !file) {
        setError('Please enter a query or upload an image for hybrid routing.')
        return;
      }
    }

    setLoading(true)
    setError('')
    setResponse(null)

    try {
      let res;
      const baseApiUrl = 'http://127.0.0.1:8000';

      if (queryMode === 'hybrid') {
        const formData = new FormData()
        if (query.trim()) formData.append('query', query)
        if (file) formData.append('file', file)
        formData.append('top_k', topK)
        if (categoryFilter) formData.append('category', categoryFilter)
        if (districtFilter) formData.append('district', districtFilter)
        if (maxFeeFilter) formData.append('max_fee', maxFeeFilter)
        if (difficultyFilter) formData.append('difficulty', difficultyFilter)

        res = await fetch(`${baseApiUrl}/query/hybrid`, {
          method: 'POST',
          body: formData,
        })
      } else if (queryMode === 'structured') {
        const params = new URLSearchParams()
        if (query.trim()) {
          params.append('generate_answer', 'true')
          params.append('question', query)
        } else {
          params.append('generate_answer', 'false')
        }
        if (categoryFilter) params.append('category', categoryFilter)
        if (districtFilter) params.append('district', districtFilter)
        if (maxFeeFilter) params.append('max_fee', maxFeeFilter)
        if (difficultyFilter) params.append('difficulty', difficultyFilter)

        res = await fetch(`${baseApiUrl}/query/structured?${params.toString()}`)
      } else if (queryMode === 'semantic') {
        const params = new URLSearchParams()
        params.append('query', query)
        params.append('top_k', topK.toString())
        params.append('generate_answer', 'true')

        res = await fetch(`${baseApiUrl}/query/semantic?${params.toString()}`)
      } else if (queryMode === 'image') {
        const formData = new FormData()
        if (file) formData.append('file', file)
        if (textQueryFilter.trim()) formData.append('text_query', textQueryFilter)
        formData.append('top_k', topK)
        formData.append('generate_answer', 'true')
        if (query.trim()) formData.append('question', query)

        res = await fetch(`${baseApiUrl}/query/image`, {
          method: 'POST',
          body: formData,
        })
      }

      if (!res.ok) {
        const errText = await res.text()
        throw new Error(errText || 'Search failed. Please verify the backend is running.')
      }

      const data = await res.json()
      setResponse(data)

      // Set raw results tab active if hybrid returns items
      if (data.sources_used) {
        if (data.sources_used.semantic) {
          setActiveTab('semantic')
        } else if (data.sources_used.structured) {
          setActiveTab('structured')
        } else if (data.sources_used.image) {
          setActiveTab('image')
        }
      }
    } catch (err) {
      setError(err.message || 'An error occurred during search.')
    } finally {
      setLoading(false)
    }
  }

  // Extract all unique attraction results across modes
  const getUniqueAttractions = () => {
    if (!response) return []
    if (response.results) {
      return response.results
    }
    if (response.raw_results) {
      const map = new Map()
      ;(response.raw_results.structured || []).forEach(a => map.set(a.id, a))
      ;(response.raw_results.semantic || []).forEach(a => map.set(a.id, a))
      if (response.raw_results.image && response.raw_results.image.attractions) {
        response.raw_results.image.attractions.forEach(a => map.set(a.id, a))
      }
      return Array.from(map.values())
    }
    return []
  }

  const attractions = getUniqueAttractions()

  return (
    <div className="app-container">
      <Header />

      <main className="main-content">
        <ModeSelector 
          queryMode={queryMode} 
          setQueryMode={setQueryMode} 
          setError={setError} 
        />

        <div className="search-section card glass">
          <form onSubmit={handleSubmit} className="search-form">
            {queryMode === 'structured' && (
              <StructuredFilters
                categoryFilter={categoryFilter}
                setCategoryFilter={setCategoryFilter}
                districtFilter={districtFilter}
                setDistrictFilter={setDistrictFilter}
                maxFeeFilter={maxFeeFilter}
                setMaxFeeFilter={setMaxFeeFilter}
                difficultyFilter={difficultyFilter}
                setDifficultyFilter={setDifficultyFilter}
              />
            )}

            {queryMode === 'image' && (
              <ImageFilters
                file={file}
                handleFileChange={handleFileChange}
                handleClearFile={handleClearFile}
                textQueryFilter={textQueryFilter}
                setTextQueryFilter={setTextQueryFilter}
              />
            )}

            {queryMode === 'hybrid' && (
              <>
                <ImageFilters
                  file={file}
                  handleFileChange={handleFileChange}
                  handleClearFile={handleClearFile}
                  textQueryFilter={textQueryFilter}
                  setTextQueryFilter={setTextQueryFilter}
                  showTextQuery={false}
                />

                <StructuredFilters
                  categoryFilter={categoryFilter}
                  setCategoryFilter={setCategoryFilter}
                  districtFilter={districtFilter}
                  setDistrictFilter={setDistrictFilter}
                  maxFeeFilter={maxFeeFilter}
                  setMaxFeeFilter={setMaxFeeFilter}
                  difficultyFilter={difficultyFilter}
                  setDifficultyFilter={setDifficultyFilter}
                />
              </>
            )}

            {/* Main Prompt/Question box (applicable to all modes) */}
            <div className="form-group">
              <label htmlFor="query-input">
                {queryMode === 'structured' && "Ask a question based on structured results (Optional)"}
                {queryMode === 'semantic' && "Semantic search query (Required)"}
                {queryMode === 'image' && "Ask a question based on visual matches (Optional)"}
                {queryMode === 'hybrid' && "Natural language query (Optional if image uploaded)"}
              </label>
              <input
                id="query-input"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  queryMode === 'structured' 
                    ? "e.g. Which attraction has the cheapest entry fee?"
                    : "e.g. waterfalls in Kandy with easy trekking difficulty..."
                }
                className="input-text"
              />
            </div>

            <div className="form-row">
              {queryMode !== 'structured' && (
                <div className="form-group flex-1">
                  <label htmlFor="top-k-select">Retrieval Limit (Top K)</label>
                  <select
                    id="top-k-select"
                    value={topK}
                    onChange={(e) => setTopK(Number(e.target.value))}
                    className="input-select"
                  >
                    <option value={2}>2 Results</option>
                    <option value={3}>3 Results</option>
                    <option value={5}>5 Results</option>
                  </select>
                </div>
              )}
            </div>

            <button type="submit" disabled={loading} className="btn-search">
              {loading ? (
                <span className="loading-spinner"></span>
              ) : (
                queryMode === 'hybrid' ? 'Classify & Search' : 'Run Search'
              )}
            </button>
          </form>

          <Presets presets={presets} handlePresetClick={handlePresetClick} />
        </div>

        {error && (
          <div className="error-banner card">
            <span className="error-icon">⚠️</span>
            <p className="error-text">{error}</p>
          </div>
        )}

        {loading && (
          <div className="skeleton-loading card glass">
            <div className="skeleton-line title"></div>
            <div className="skeleton-line block"></div>
            <div className="skeleton-line block"></div>
          </div>
        )}

        {response && (
          <ResultsView
            response={response}
            attractions={attractions}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
          />
        )}
      </main>
    </div>
  )
}

export default App
