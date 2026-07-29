export default function AttractionCard({ attraction, imageDetail, sources }) {
  const getCategoryFolder = (category) => {
    if (!category) return 'waterfalls';
    const cat = category.toLowerCase();
    if (cat === 'beach') return 'beaches';
    if (cat === 'mountain') return 'mountains';
    return 'waterfalls';
  }

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
