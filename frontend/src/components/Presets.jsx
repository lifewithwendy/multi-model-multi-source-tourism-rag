export default function Presets({ presets, handlePresetClick }) {
  return (
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
  );
}
