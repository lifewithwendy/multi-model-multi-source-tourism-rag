export default function ImageFilters({
  file,
  handleFileChange,
  handleClearFile,
  textQueryFilter,
  setTextQueryFilter,
  showTextQuery = true
}) {
  return (
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

      {showTextQuery && (
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
      )}
    </div>
  );
}
