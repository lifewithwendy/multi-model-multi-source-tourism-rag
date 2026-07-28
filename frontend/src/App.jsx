import { useState } from 'react'
import './App.css'

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
      <header className="app-header">
        <div className="badge-sri-lanka">🇱🇰 Sri Lanka Tourism</div>
        <h1>Multimodal Hybrid RAG</h1>
        <p className="subtitle">
          Query structured Postgres data, semantic descriptions, and visual image collections using AI
        </p>
      </header>

      <main className="main-content">
        {/* Mode Selector Tabs */}
        <div className="mode-selector-container card glass">
          <h3>Select Query Mode</h3>
          <div className="mode-tabs">
            <button
              onClick={() => { setQueryMode('hybrid'); setError(''); }}
              className={`mode-btn ${queryMode === 'hybrid' ? 'active' : ''}`}
            >
              🧠 Hybrid Mode
            </button>
            <button
              onClick={() => { setQueryMode('structured'); setError(''); }}
              className={`mode-btn ${queryMode === 'structured' ? 'active' : ''}`}
            >
              📊 Structured Mode
            </button>
            <button
              onClick={() => { setQueryMode('semantic'); setError(''); }}
              className={`mode-btn ${queryMode === 'semantic' ? 'active' : ''}`}
            >
              📖 Semantic Mode
            </button>
            <button
              onClick={() => { setQueryMode('image'); setError(''); }}
              className={`mode-btn ${queryMode === 'image' ? 'active' : ''}`}
            >
              🖼️ Image Mode
            </button>
          </div>
        </div>

        <div className="search-section card glass">
          <form onSubmit={handleSubmit} className="search-form">
            {/* Context-specific input forms */}
            {queryMode === 'structured' && (
              <div className="structured-filters-grid">
                <div className="form-group">
                  <label htmlFor="category-select">Category</label>
                  <select
                    id="category-select"
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                    className="input-select"
                  >
                    <option value="">Any Category</option>
                    <option value="Waterfall">Waterfall</option>
                    <option value="Mountain">Mountain</option>
                    <option value="beach">Beach</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="district-select">District</label>
                  <select
                    id="district-select"
                    value={districtFilter}
                    onChange={(e) => setDistrictFilter(e.target.value)}
                    className="input-select"
                  >
                    <option value="">Any District</option>
                    <option value="Badulla">Badulla</option>
                    <option value="Nuwara Eliya">Nuwara Eliya</option>
                    <option value="Ratnapura">Ratnapura</option>
                    <option value="Kegalle">Kegalle</option>
                    <option value="Kandy">Kandy</option>
                    <option value="Matale">Matale</option>
                    <option value="Matara">Matara</option>
                    <option value="Galle">Galle</option>
                    <option value="Ampara">Ampara</option>
                    <option value="Trincomalee">Trincomalee</option>
                    <option value="Batticaloa">Batticaloa</option>
                    <option value="Hambantota">Hambantota</option>
                    <option value="Gampaha">Gampaha</option>
                    <option value="Puttalam">Puttalam</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="max-fee-input">Max Entrance Fee (LKR)</label>
                  <input
                    id="max-fee-input"
                    type="number"
                    value={maxFeeFilter}
                    placeholder="e.g. 500"
                    onChange={(e) => setMaxFeeFilter(e.target.value)}
                    className="input-text"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="difficulty-select">Difficulty</label>
                  <select
                    id="difficulty-select"
                    value={difficultyFilter}
                    onChange={(e) => setDifficultyFilter(e.target.value)}
                    className="input-select"
                  >
                    <option value="">Any Difficulty</option>
                    <option value="Easy">Easy</option>
                    <option value="Moderate">Moderate</option>
                    <option value="Strenuous">Strenuous</option>
                  </select>
                </div>
              </div>
            )}

            {queryMode === 'image' && (
              <div className="form-row">
                <div className="form-group flex-2">
                  <label>Upload Reference Image</label>
                  <div className={`file-upload-zone ${file ? 'has-file' : ''}`}>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleFileChange}
                      className="file-input-hidden"
                      id="file-upload"
                    />
                    <label htmlFor="file-upload" className="file-upload-label">
                      {file ? (
                        <div className="file-info">
                          <span className="file-icon">🖼️</span>
                          <span className="file-name">{file.name}</span>
                          <button type="button" onClick={handleClearFile} className="btn-clear-file">✕</button>
                        </div>
                      ) : (
                        <span className="placeholder-text">Click to choose or drag reference image here</span>
                      )}
                    </label>
                  </div>
                </div>

                <div className="form-group flex-1">
                  <label htmlFor="text-query-input">Or Describe Visuals (Text-to-Image)</label>
                  <input
                    id="text-query-input"
                    type="text"
                    value={textQueryFilter}
                    onChange={(e) => setTextQueryFilter(e.target.value)}
                    placeholder="e.g. golden sand palm trees"
                    className="input-text"
                  />
                </div>
              </div>
            )}

            {queryMode === 'hybrid' && (
              <>
                <div className="form-row">
                  <div className="form-group flex-2">
                    <label>Upload Reference Image (Optional)</label>
                    <div className={`file-upload-zone ${file ? 'has-file' : ''}`}>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="file-input-hidden"
                        id="file-upload"
                      />
                      <label htmlFor="file-upload" className="file-upload-label">
                        {file ? (
                          <div className="file-info">
                            <span className="file-icon">🖼️</span>
                            <span className="file-name">{file.name}</span>
                            <button type="button" onClick={handleClearFile} className="btn-clear-file">✕</button>
                          </div>
                        ) : (
                          <span className="placeholder-text">Click to choose or drag image here</span>
                        )}
                      </label>
                    </div>
                  </div>
                </div>

                <div className="structured-filters-grid">
                  <div className="form-group">
                    <label htmlFor="category-select">Category</label>
                    <select
                      id="category-select"
                      value={categoryFilter}
                      onChange={(e) => setCategoryFilter(e.target.value)}
                      className="input-select"
                    >
                      <option value="">Any Category</option>
                      <option value="Waterfall">Waterfall</option>
                      <option value="Mountain">Mountain</option>
                      <option value="beach">Beach</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="district-select">District</label>
                    <select
                      id="district-select"
                      value={districtFilter}
                      onChange={(e) => setDistrictFilter(e.target.value)}
                      className="input-select"
                    >
                      <option value="">Any District</option>
                      <option value="Badulla">Badulla</option>
                      <option value="Nuwara Eliya">Nuwara Eliya</option>
                      <option value="Ratnapura">Ratnapura</option>
                      <option value="Kegalle">Kegalle</option>
                      <option value="Kandy">Kandy</option>
                      <option value="Matale">Matale</option>
                      <option value="Matara">Matara</option>
                      <option value="Galle">Galle</option>
                      <option value="Ampara">Ampara</option>
                      <option value="Trincomalee">Trincomalee</option>
                      <option value="Batticaloa">Batticaloa</option>
                      <option value="Hambantota">Hambantota</option>
                      <option value="Gampaha">Gampaha</option>
                      <option value="Puttalam">Puttalam</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="max-fee-input">Max Entrance Fee (LKR)</label>
                    <input
                      id="max-fee-input"
                      type="number"
                      value={maxFeeFilter}
                      placeholder="e.g. 500"
                      onChange={(e) => setMaxFeeFilter(e.target.value)}
                      className="input-text"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="difficulty-select">Difficulty</label>
                    <select
                      id="difficulty-select"
                      value={difficultyFilter}
                      onChange={(e) => setDifficultyFilter(e.target.value)}
                      className="input-select"
                    >
                      <option value="">Any Difficulty</option>
                      <option value="Easy">Easy</option>
                      <option value="Moderate">Moderate</option>
                      <option value="Strenuous">Strenuous</option>
                    </select>
                  </div>
                </div>
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

          <div className="presets-container">
            <span className="presets-title">Try Example Presets:</span>
            <div className="preset-buttons">
              {presets.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handlePresetClick(p)}
                  className="btn-preset"
                  type="button"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
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
          <div className="results-container">
            {/* Show Classifier card in Hybrid mode */}
            {response.sources_used && (
              <div className="routing-card card glass">
                <h3>🧠 Classifier Routing</h3>
                <div className="routing-badges">
                  <div className={`badge ${response.sources_used.structured ? 'active' : 'inactive'}`}>
                    Structured {response.sources_used.structured ? '🟢' : '⚪'}
                  </div>
                  <div className={`badge ${response.sources_used.semantic ? 'active' : 'inactive'}`}>
                    Semantic {response.sources_used.semantic ? '🟢' : '⚪'}
                  </div>
                  <div className={`badge ${response.sources_used.image ? 'active' : 'inactive'}`}>
                    Image {response.sources_used.image ? '🟢' : '⚪'}
                  </div>
                </div>
                <p className="routing-reason">{response.sources_used.reason}</p>
              </div>
            )}

            {/* Generated LLM Answer */}
            {response.answer && (
              <div className="answer-card card glass">
                <h3>🤖 Assistant Answer</h3>
                <div className="answer-content">
                  {response.answer}
                </div>
              </div>
            )}

            {/* Matched Attractions Grid */}
            <div className="attraction-results card glass">
              <h3>🔍 Retrieved Attractions ({attractions.length})</h3>
              {attractions.length === 0 ? (
                <p className="no-data">No matching attractions were retrieved.</p>
              ) : (
                <div className="attraction-grid">
                  {attractions.map((attr) => (
                    <AttractionCard 
                      key={attr.id} 
                      attraction={attr} 
                      sources={response.attraction_sources ? response.attraction_sources[attr.id] : null}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Raw Context Tabs (Only for Hybrid mode) */}
            {response.raw_results && (
              <div className="raw-results-card card glass">
                <div className="tabs-header">
                  <h3>🔍 Raw Retrieval Context (by source)</h3>
                  <div className="tab-buttons">
                    <button
                      onClick={() => setActiveTab('semantic')}
                      className={`tab-btn ${activeTab === 'semantic' ? 'active' : ''}`}
                      disabled={!response.sources_used.semantic}
                    >
                      Semantic Text ({response.raw_results.semantic.length})
                    </button>
                    <button
                      onClick={() => setActiveTab('structured')}
                      className={`tab-btn ${activeTab === 'structured' ? 'active' : ''}`}
                      disabled={!response.sources_used.structured}
                    >
                      Structured DB ({response.raw_results.structured.length})
                    </button>
                    <button
                      onClick={() => setActiveTab('image')}
                      className={`tab-btn ${activeTab === 'image' ? 'active' : ''}`}
                      disabled={!response.sources_used.image}
                    >
                      Image Matches ({response.raw_results.image?.attractions?.length || 0})
                    </button>
                  </div>
                </div>

                <div className="tab-content">
                  {activeTab === 'semantic' && (
                    <div className="attraction-grid">
                      {response.raw_results.semantic.length === 0 ? (
                        <p className="no-data">No semantic results retrieved.</p>
                      ) : (
                        response.raw_results.semantic.map((attr) => (
                          <AttractionCard key={attr.id} attraction={attr} />
                        ))
                      )}
                    </div>
                  )}

                  {activeTab === 'structured' && (
                    <div className="attraction-grid">
                      {response.raw_results.structured.length === 0 ? (
                        <p className="no-data">No structured database results retrieved.</p>
                      ) : (
                        response.raw_results.structured.map((attr) => (
                          <AttractionCard key={attr.id} attraction={attr} />
                        ))
                      )}
                    </div>
                  )}

                  {activeTab === 'image' && (
                    <div className="attraction-grid">
                      {!response.raw_results.image || response.raw_results.image.attractions.length === 0 ? (
                        <p className="no-data">No visually matching attractions retrieved.</p>
                      ) : (
                        response.raw_results.image.attractions.map((attr, idx) => (
                          <AttractionCard
                            key={attr.id}
                            attraction={attr}
                            imageDetail={{
                              imageId: response.raw_results.image.image_ids[idx],
                              distance: response.raw_results.image.distances[idx]
                            }}
                          />
                        ))
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

function AttractionCard({ attraction, imageDetail, sources }) {
  // Map singular category to plural directory name
  const getCategoryFolder = (category) => {
    if (!category) return 'waterfalls';
    const cat = category.toLowerCase();
    if (cat === 'beach') return 'beaches';
    if (cat === 'mountain') return 'mountains';
    return 'waterfalls';
  }

  // Construct image source URL
  const imageUrl = attraction.images && attraction.images.length > 0
    ? `http://127.0.0.1:8000/images/${getCategoryFolder(attraction.category)}/${attraction.images[0]}`
    : null;

  return (
    <div className="attraction-card">
      {imageUrl && (
        <div className="attraction-card-image-container">
          <img 
            src={imageUrl} 
            alt={attraction.name} 
            className="attraction-card-image"
            onError={(e) => {
              // Hide image if it fails to load
              e.target.style.display = 'none';
            }}
          />
        </div>
      )}
      <div className="card-header">
        <h4>{attraction.name}</h4>
        <span className={`category-badge ${attraction.category.toLowerCase()}`}>
          {attraction.category}
        </span>
      </div>
      
      {/* Individual card source badges */}
      {sources && sources.length > 0 && (
        <div className="card-source-badges">
          {sources.map((src, i) => (
            <span key={i} className={`card-source-badge source-${src}`}>
              {src === 'structured' && '📊 DB'}
              {src === 'semantic' && '📖 Semantic'}
              {src === 'image' && '🖼️ Image Search'}
            </span>
          ))}
        </div>
      )}

      <div className="card-meta">
        <span>📍 {attraction.district}, {attraction.province}</span>
        {attraction.entrance_fee_lkr !== undefined && (
          <span>💵 Fee: {attraction.entrance_fee_lkr} LKR</span>
        )}
        {attraction.trekking_difficulty && (
          <span>🥾 Trek: {attraction.trekking_difficulty}</span>
        )}
        {attraction.best_season && (
          <span>📅 Season: {attraction.best_season}</span>
        )}
      </div>
      {attraction.description && (
        <p className="card-description">{attraction.description}</p>
      )}
      {imageDetail && (
        <div className="image-match-detail">
          <span>🖼️ Image ID: {imageDetail.imageId}</span>
          {imageDetail.distance !== undefined && (
            <span>Similarity: {(1 - imageDetail.distance).toFixed(4)}</span>
          )}
        </div>
      )}
    </div>
  )
}

export default App
