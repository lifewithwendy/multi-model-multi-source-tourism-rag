export default function StructuredFilters({
  categoryFilter,
  setCategoryFilter,
  districtFilter,
  setDistrictFilter,
  maxFeeFilter,
  setMaxFeeFilter,
  difficultyFilter,
  setDifficultyFilter
}) {
  return (
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
  );
}
