import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getAdminAgentsGeo } from '../lib/api';
import type { AdminAgentGeoPoint } from '../lib/types';

// Fix default Leaflet marker icons broken by Vite's asset pipeline
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

// Extend Leaflet types for the heat plugin
declare module 'leaflet' {
  function heatLayer(
    latlngs: [number, number, number][],
    options?: { radius?: number; blur?: number; maxZoom?: number; max?: number; gradient?: Record<string, string> }
  ): L.Layer;
}

type ViewMode = 'markers' | 'heatmap';

function HeatmapLayer({ points }: { points: [number, number, number][] }) {
  const map = useMap();
  const layerRef = useRef<L.Layer | null>(null);

  useEffect(() => {
    // Dynamically import leaflet.heat (side-effect import extends L)
    import('leaflet.heat').then(() => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
      }
      if (points.length === 0) return;
      const heat = L.heatLayer(points, {
        radius: 30,
        blur: 20,
        maxZoom: 8,
        gradient: { 0.2: '#8b5cf6', 0.5: '#ff314a', 1.0: '#ff8c00' },
      });
      heat.addTo(map);
      layerRef.current = heat;
    }).catch(() => {/* silently skip if heat unavailable */});

    return () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
        layerRef.current = null;
      }
    };
  }, [map, points]);

  return null;
}

interface Props {
  adminToken: string;
}

export default function AdminAgentMap({ adminToken }: Props) {
  const [agents, setAgents] = useState<AdminAgentGeoPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('markers');

  useEffect(() => {
    getAdminAgentsGeo(adminToken)
      .then(setAgents)
      .catch(() => setAgents([]))
      .finally(() => setLoading(false));
  }, [adminToken]);

  const countrySet = new Set(agents.map((a) => a.country).filter(Boolean));
  const heatPoints: [number, number, number][] = agents.map((a) => [a.lat, a.lon, 1]);

  return (
    <div className="rounded-2xl border border-white/10 bg-black/30 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
        <div>
          <h2 className="text-sm font-semibold tracking-widest uppercase text-paper/60">Agent Origins</h2>
          {!loading && agents.length > 0 && (
            <p className="text-xs text-paper/40 mt-0.5">
              {agents.length} agent{agents.length !== 1 ? 's' : ''} mapped
              {countrySet.size > 0 && ` across ${countrySet.size} countr${countrySet.size !== 1 ? 'ies' : 'y'}`}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('markers')}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              viewMode === 'markers'
                ? 'bg-coral text-white'
                : 'bg-white/10 text-paper/60 hover:bg-white/20'
            }`}
          >
            Markers
          </button>
          <button
            onClick={() => setViewMode('heatmap')}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              viewMode === 'heatmap'
                ? 'bg-coral text-white'
                : 'bg-white/10 text-paper/60 hover:bg-white/20'
            }`}
          >
            Heatmap
          </button>
        </div>
      </div>

      {/* Map */}
      <div className="relative" style={{ height: '420px' }}>
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center bg-black/20">
            <div className="brand-spinner" />
          </div>
        ) : agents.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center text-paper/40 text-sm">
            No geo data yet — agents registered from localhost have no coordinates.
          </div>
        ) : (
          <MapContainer
            center={[20, 0]}
            zoom={2}
            minZoom={1}
            maxZoom={18}
            style={{ height: '100%', width: '100%', background: '#0a0a0f' }}
            className="agent-map"
          >
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://carto.com/">CARTO</a>'
              maxZoom={19}
            />

            {viewMode === 'markers' && (
              <MarkerClusterGroup
                chunkedLoading
                maxClusterRadius={60}
                showCoverageOnHover={false}
              >
                {agents.map((agent) => (
                  <Marker key={agent.id} position={[agent.lat, agent.lon]}>
                    <Popup>
                      <div style={{ fontFamily: 'Space Grotesk, sans-serif', minWidth: '160px' }}>
                        <strong style={{ display: 'block', marginBottom: '4px' }}>{agent.display_name}</strong>
                        <span style={{ fontSize: '11px', color: '#888', display: 'block' }}>{agent.archetype}</span>
                        {(agent.city || agent.country) && (
                          <span style={{ fontSize: '11px', color: '#aaa', display: 'block', marginTop: '2px' }}>
                            {[agent.city, agent.country].filter(Boolean).join(', ')}
                          </span>
                        )}
                        <a
                          href={`/admin/agent/${agent.id}`}
                          style={{ fontSize: '11px', color: '#ff314a', display: 'block', marginTop: '6px' }}
                        >
                          View agent →
                        </a>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MarkerClusterGroup>
            )}

            {viewMode === 'heatmap' && <HeatmapLayer points={heatPoints} />}
          </MapContainer>
        )}
      </div>
    </div>
  );
}
