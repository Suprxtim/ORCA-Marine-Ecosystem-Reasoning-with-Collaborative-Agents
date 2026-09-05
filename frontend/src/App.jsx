import { useState, useRef, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, GeoJSON, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { ShieldAlert, Ship, CloudRain, Activity, Send, Loader2, Layers } from 'lucide-react';
import './index.css';

// Fix Leaflet marker icons
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

export default function App() {
  const [query, setQuery] = useState("");
  const [chatHistory, setChatHistory] = useState([{ role: "agent", text: "ORCA Maritime AI initialized. How can I assist you today?" }]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [reasoningTrace, setReasoningTrace] = useState([]);
  const [mapCenter, setMapCenter] = useState([22.0, 69.5]); // Default near Harbor_Point/Gujarat
  const [mapLayers, setMapLayers] = useState([]);
  const [language, setLanguage] = useState("English");

  const toggleLayer = (id) => {
    setMapLayers(prev => prev.map(l => l.id === id ? { ...l, visible: !l.visible } : l));
  };

  const handleSend = async () => {
    if (!query.trim() || isProcessing) return;
    
    const userQuery = query;
    setChatHistory(prev => [...prev, { role: "user", text: userQuery }]);
    setQuery("");
    setIsProcessing(true);
    setReasoningTrace([{ status: "in-progress", agent: "Orchestrator", detail: "Analyzing intent and assigning agents..." }]);

    try {
      const response = await fetch("http://127.0.0.1:8001/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userQuery, target_language: language })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let finalAgentResponse = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.substring(6);
            if (dataStr === "[DONE]") {
              setIsProcessing(false);
              break;
            }
            try {
              const data = JSON.parse(dataStr);
              if (data.error) {
                 setChatHistory(prev => [...prev, { role: "agent", text: `Error: ${data.error}`, isError: true }]);
                 break;
              }
              
              // Handle LangGraph streaming events
              if (data.event === "on_chat_model_stream") {
                 // The models stream tokens. 
                 if (data.content) {
                    finalAgentResponse += data.content;
                 }
              } else if (data.event === "on_tool_start") {
                 setReasoningTrace(prev => [
                   ...prev, 
                   { status: "in-progress", agent: "Agent Tool", detail: `Calling ${data.name}...` }
                 ]);
              } else if (data.event === "on_tool_end") {
                 let formattedDetails = `Finished ${data.name}.`;
                 if (data.output) {
                    try {
                        const parsed = JSON.parse(data.output.content || data.output);
                        if (parsed && typeof parsed === 'object' && !parsed.error) {
                            const entries = [];
                            for (const [key, value] of Object.entries(parsed)) {
                                if (key.endsWith('_source') || key.endsWith('_low_confidence') || key === 'matched_location' || key === 'distance_km') continue;
                                const sourceKey = `${key.split('_')[0]}_source`;
                                const confKey = `${key.split('_')[0]}_low_confidence`;
                                const source = parsed[sourceKey] || parsed['source'] || '';
                                const confWarning = parsed[confKey] ? ' ⚠️ Low Conf (>20km)' : '';
                                
                                let label = key.replace(/_/g, ' ');
                                entries.push(`• ${label}: ${value} ${source ? `(${source}${confWarning})` : ''}`);
                            }
                            if (entries.length > 0) {
                                formattedDetails = entries.join('\n');
                            }
                        }
                    } catch(e) {}
                 }
                 
                 setReasoningTrace(prev => [
                   ...prev.map(t => t.status === "in-progress" ? { ...t, status: "done" } : t),
                   { status: "done", agent: data.name, detail: formattedDetails }
                 ]);
              } else if (data.event === "on_layers_ready") {
                 setMapLayers(data.layers);
                 if (data.layers.length > 0) {
                     const firstLayer = data.layers[0];
                     if (firstLayer.type === "point" || firstLayer.type === "circle") {
                         setMapCenter([firstLayer.geojson.coordinates[1], firstLayer.geojson.coordinates[0]]);
                     }
                 }
              }
            } catch (e) {
              console.error("Error parsing SSE JSON", e, dataStr);
            }
          }
        }
      }

      if (finalAgentResponse) {
         setChatHistory(prev => [...prev, { role: "agent", text: finalAgentResponse }]);
         setReasoningTrace(prev => [...prev, { status: "done", agent: "Risk Agent", detail: "Verdict reached." }]);
      }

    } catch (err) {
      console.error(err);
      setChatHistory(prev => [...prev, { role: "agent", text: "Connection to ORCA failed.", isError: true }]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="app-container">
      {/* LEFT: CHAT PANEL */}
      <div className="glass-panel chat-column">
        <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Ship size={20} /> ORCA Terminal
          </div>
          <select 
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            style={{
              background: 'rgba(0, 0, 0, 0.4)',
              color: 'var(--text-primary)',
              border: '1px solid var(--panel-border)',
              borderRadius: '4px',
              padding: '2px 8px',
              fontSize: '0.85rem'
            }}
          >
            <option value="English">English</option>
            <option value="Hindi">हिंदी (Hindi)</option>
          </select>
        </div>
        
        <div style={{ flex: 1, padding: "1rem", overflowY: "auto", display: "flex", flexDirection: "column", gap: "1rem" }}>
          {chatHistory.map((msg, i) => (
            <div key={i} style={{
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              background: msg.role === "user" ? "rgba(0, 200, 255, 0.2)" : (msg.isError ? "var(--alert-bg)" : "rgba(16, 30, 60, 0.8)"),
              border: `1px solid ${msg.role === "user" ? "var(--accent)" : (msg.isError ? "var(--alert-red)" : "var(--panel-border)")}`,
              padding: "0.8rem",
              borderRadius: "8px",
              maxWidth: "85%",
              whiteSpace: "pre-wrap"
            }}>
              <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "4px" }}>
                {msg.role === "user" ? "Captain" : "ORCA AI"}
              </div>
              {msg.text}
            </div>
          ))}
          {isProcessing && (
            <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--accent)" }}>
              <Loader2 className="animate-spin" size={16} /> Processing...
            </div>
          )}
        </div>

        <div style={{ padding: "1rem", borderTop: "1px solid var(--panel-border)", display: "flex", gap: "0.5rem" }}>
          <input 
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="E.g., Is it safe near Harbor_Point?"
            style={{
              flex: 1,
              background: "rgba(0, 0, 0, 0.3)",
              border: "1px solid var(--panel-border)",
              color: "white",
              padding: "0.8rem",
              borderRadius: "6px",
              outline: "none"
            }}
          />
          <button onClick={handleSend} style={{
            background: "var(--accent)",
            color: "var(--bg-dark)",
            border: "none",
            borderRadius: "6px",
            padding: "0 1rem",
            cursor: "pointer",
            fontWeight: "bold"
          }}>
            <Send size={18} />
          </button>
        </div>
      </div>

      {/* CENTER: MAP PANEL */}
      <div className="glass-panel map-column">
        <div className="panel-header">
          <Activity size={20} /> Live Maritime Map
        </div>
        <div style={{ flex: 1, position: "relative" }}>
          <div style={{
            position: 'absolute', top: 10, right: 10, zIndex: 1000,
            background: 'rgba(10, 17, 40, 0.9)', padding: '10px', borderRadius: '8px', border: '1px solid var(--panel-border)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '8px', fontWeight: 'bold' }}>
              <Layers size={16}/> Layers
            </div>
            {mapLayers.map((layer) => (
              <div key={layer.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', marginBottom: '4px' }}>
                <input type="checkbox" checked={layer.visible} onChange={() => toggleLayer(layer.id)} style={{ cursor: 'pointer' }} />
                <span style={{ color: layer.style?.color || 'white' }}>{layer.label}</span>
              </div>
            ))}
            {mapLayers.length === 0 && <div style={{ fontSize: '0.8rem', color: 'gray' }}>No data layers</div>}
          </div>
          <MapContainer center={mapCenter} zoom={6} style={{ height: "100%", width: "100%", background: "#0a1128", zIndex: 1 }}>
            <TileLayer
              url="https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>'
            />
            {mapLayers.filter(l => l.visible).map(layer => {
              if (layer.type === "point") {
                return (
                  <CircleMarker 
                    key={layer.id} 
                    center={[layer.geojson.coordinates[1], layer.geojson.coordinates[0]]} 
                    radius={layer.style?.radius || 10}
                    pathOptions={{ color: layer.style?.color || 'blue', fillColor: layer.style?.color || 'blue', fillOpacity: 0.8 }}
                  >
                    <Popup>{layer.label}</Popup>
                  </CircleMarker>
                );
              } else if (layer.type === "circle") {
                return (
                  <Circle 
                    key={layer.id} 
                    center={[layer.geojson.coordinates[1], layer.geojson.coordinates[0]]} 
                    radius={layer.style?.radius || 20000} 
                    pathOptions={{ color: layer.style?.color || 'red', fillColor: layer.style?.color || 'red', fillOpacity: 0.4 }} 
                  >
                    <Popup>{layer.label}</Popup>
                  </Circle>
                );
              } else if (layer.type === "polygon") {
                // Ensure geojson is wrapped as a Feature for React Leaflet GeoJSON component
                const feature = { type: "Feature", properties: { name: layer.label }, geometry: layer.geojson };
                return (
                  <GeoJSON 
                    key={layer.id + JSON.stringify(layer.geojson.coordinates)} 
                    data={feature} 
                    pathOptions={layer.style} 
                  />
                );
              }
              return null;
            })}
          </MapContainer>
        </div>
      </div>

      {/* RIGHT: REASONING & ALERTS PANEL */}
      <div className="glass-panel reasoning-column">
        <div className="panel-header">
          <ShieldAlert size={20} /> Reasoning Trace
        </div>
        <div style={{ padding: "1rem", flex: 1, overflowY: "auto" }}>
          {reasoningTrace.length === 0 ? (
            <div style={{ color: "var(--text-secondary)", fontStyle: "italic", textAlign: "center", marginTop: "2rem" }}>
              Waiting for queries to trace agent steps...
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {reasoningTrace.map((trace, i) => (
                <div key={i} style={{
                  padding: "0.8rem",
                  background: "rgba(0, 0, 0, 0.2)",
                  borderLeft: `3px solid ${trace.status === "done" ? "var(--success)" : "var(--accent)"}`,
                  borderRadius: "4px"
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                    <strong style={{ color: "white" }}>{trace.agent}</strong>
                    {trace.status === "in-progress" && <Loader2 className="animate-spin" size={14} style={{ color: "var(--accent)" }}/>}
                  </div>
                  <div style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>
                    {trace.detail}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
