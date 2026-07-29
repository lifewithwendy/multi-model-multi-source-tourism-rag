import AttractionCard from './AttractionCard';

export default function ResultsView({ response, attractions, activeTab, setActiveTab }) {
  return (
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
  );
}
