export default function ModeSelector({ queryMode, setQueryMode, setError }) {
  const modes = [
    { id: 'hybrid', label: '🧠 Hybrid Mode' },
    { id: 'structured', label: '📊 Structured Mode' },
    { id: 'semantic', label: '📖 Semantic Mode' },
    { id: 'image', label: '🖼️ Image Mode' }
  ];

  return (
    <div className="mode-selector-container card glass">
      <h3>Select Query Mode</h3>
      <div className="mode-tabs">
        {modes.map((mode) => (
          <button
            key={mode.id}
            onClick={() => {
              setQueryMode(mode.id);
              setError('');
            }}
            className={`mode-btn ${queryMode === mode.id ? 'active' : ''}`}
          >
            {mode.label}
          </button>
        ))}
      </div>
    </div>
  );
}
