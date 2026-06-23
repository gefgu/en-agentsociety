import React, { useMemo, useState } from "react";
import Map, { Source, Layer } from "react-map-gl";
import { Segmented } from "antd";
import "mapbox-gl/dist/mapbox-gl.css";
import { getPalette, FONT_MONO } from "./theme";
import { useTheme } from "../../context/ThemeContext";

const MAPBOX_ACCESS_TOKEN =
  "pk.eyJ1IjoiZmh5ZHJhbGlzayIsImEiOiJja3VzMWc5NXkwb3RnMm5sbnVvd3IydGY0In0.FrwFkYIMpLbU83K9rHSe8w";

/* eslint-disable @typescript-eslint/no-explicit-any */
type StvdChart = {
  layers?: Record<string, any>;
  colors?: any;
  center?: [number, number];
  zoom?: number;
};

const StvdMap: React.FC<{ stvd: StvdChart; height?: string }> = ({ stvd, height = "560px" }) => {
  const { theme } = useTheme();
  const palette = getPalette(theme);
  const mapStyle = theme === 'dark'
    ? 'mapbox://styles/mapbox/dark-v11'
    : 'mapbox://styles/mapbox/light-v11';

  const resolutions = useMemo(
    () => Object.keys(stvd.layers || {}).sort((a, b) => Number(a) - Number(b)),
    [stvd.layers],
  );
  const [resolution, setResolution] = useState<string>(resolutions[0]);

  const featureCollection = useMemo(() => {
    const layer = stvd.layers?.[resolution] || stvd.layers?.[resolutions[0]];
    if (!layer) return { type: "FeatureCollection", features: [] };
    const features = (layer.features || []).map((f: any) => ({
      ...f,
      properties: {
        ...f.properties,
        color: f.properties?._skmobVis?.color || "#cccccc",
      },
    }));
    return { type: "FeatureCollection", features };
  }, [stvd.layers, resolution, resolutions]);

  const center = stvd.center || [0, 0];

  if (!resolutions.length) {
    return <div style={{ color: palette.muted, fontFamily: FONT_MONO }}>No STVD data.</div>;
  }

  return (
    <div style={{ position: "relative", height, width: "100%" }}>
      <div style={{ position: "absolute", zIndex: 1, top: 12, left: 12 }}>
        <Segmented
          size="small"
          value={resolution}
          onChange={(v) => setResolution(String(v))}
          options={resolutions.map((r) => ({ label: `H3 ${r}`, value: r }))}
        />
      </div>
      <Map
        mapboxAccessToken={MAPBOX_ACCESS_TOKEN}
        initialViewState={{ longitude: center[0], latitude: center[1], zoom: stvd.zoom || 10 }}
        mapStyle={mapStyle}
        style={{ width: "100%", height: "100%", borderRadius: 6 }}
      >
        <Source id="stvd" type="geojson" data={featureCollection as any}>
          <Layer
            id="stvd-fill"
            type="fill"
            paint={{ "fill-color": ["get", "color"], "fill-opacity": 0.6, "fill-outline-color": palette.axis }}
          />
        </Source>
      </Map>
    </div>
  );
};

export default StvdMap;
