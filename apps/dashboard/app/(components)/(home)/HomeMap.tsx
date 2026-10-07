"use client";

import Image from "next/image";
import Map, { Marker, NavigationControl, Popup } from "react-map-gl/maplibre";
import { setWorkerUrl } from "maplibre-gl";
import { toNum } from "@fiery/utils";
import { VolcanoDashboard, TrainingSignal } from "@fiery/types";
import { VOLCANO_SPRITE } from "@/lib/constants";
import { TEST_IDS } from "@/lib/test-ids";
import { inferenceRequest } from "@/lib/utils";
import { HomeVolcano } from "./HomeVolcano";

setWorkerUrl("/maplibre/maplibre-gl-worker.mjs");

const SVZ_BOUNDS: [[number, number], [number, number]] = [
  [-76, -47],
  [-70, -32],
];

type HomeMapProps = {
  userId: string;
  volcanoes: readonly VolcanoDashboard[];
  selectedId: string | null;
  onSelect: (volcanoId: string | null) => void;
  isMobile: boolean;
};

export function HomeMap({
  userId,
  volcanoes,
  selectedId,
  onSelect,
  isMobile,
}: HomeMapProps) {
  const longitudes = volcanoes.map((volcano) => toNum(volcano.longitude));
  const latitudes = volcanoes.map((volcano) => toNum(volcano.latitude));
  const selected =
    volcanoes.find((volcano) => volcano.id === selectedId) ?? null;

  return (
    <Map
      style={{ width: "100%", height: "100%" }}
      mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
      workerUrl="/maplibre/maplibre-gl-worker.mjs"
      initialViewState={{
        bounds:
          longitudes.length && latitudes.length
            ? [
                [Math.min(...longitudes), Math.min(...latitudes)],
                [Math.max(...longitudes), Math.max(...latitudes)],
              ]
            : SVZ_BOUNDS,
        fitBoundsOptions: { padding: 48, maxZoom: 7 },
      }}
    >
      <NavigationControl position="top-right" />
      {volcanoes.map((volcano) => {
        const canInfer =
          inferenceRequest(volcano, TrainingSignal.deformation) != null ||
          inferenceRequest(volcano, TrainingSignal.seismic) != null;
        return (
          <Marker
            key={volcano.id}
            longitude={toNum(volcano.longitude)}
            latitude={toNum(volcano.latitude)}
            anchor="bottom"
            onClick={(event) => {
              event.originalEvent.stopPropagation();
              onSelect(volcano.id);
            }}
          >
            <span
              data-testid={TEST_IDS.homeMapMarker}
              className={
                canInfer
                  ? "volcano-sprite volcano-sprite--live"
                  : "volcano-sprite"
              }
            >
              <Image
                src={VOLCANO_SPRITE}
                alt={volcano.name}
                width={28}
                height={28}
                className="h-7 w-7 max-w-none"
              />
            </span>
          </Marker>
        );
      })}
      {selected ? (
        <Popup
          longitude={toNum(selected.longitude)}
          latitude={toNum(selected.latitude)}
          anchor="top"
          offset={12}
          maxWidth="320px"
          onClose={() => onSelect(null)}
        >
          <HomeVolcano userId={userId} volcano={selected} isMobile={isMobile} />
        </Popup>
      ) : null}
    </Map>
  );
}
