"use client";

import { useState } from "react";
import Image from "next/image";
import { Dot, signalLabel } from "@fiery/ui";
import { formatDecimal, formatNumber } from "@fiery/utils";
import { TrainingSignal, type VolcanoDashboard } from "@fiery/types";
import { httpSafeImageUrl } from "@/lib/utils";
import { TEST_IDS } from "@lib/test-ids";
import { IMAGE_LOADING } from "@/lib/constants";
import { HomeInference } from "./HomeInference";

type HomeVolcanoProps = {
  userId: string;
  volcano: VolcanoDashboard;
  isMobile: boolean;
};

export function HomeVolcano({ userId, volcano, isMobile }: HomeVolcanoProps) {
  const chipText = isMobile ? "text-[10px]" : "text-xs";
  const chipClass = `inline-flex items-center rounded-sm border px-2 py-0.5 font-data font-medium ${chipText}`;
  const metaText = isMobile ? "text-[11px]" : "text-xs";
  const imageSrc = httpSafeImageUrl(volcano.imagePath);
  const [failedImageSrc, setFailedImageSrc] = useState<string | null>(null);
  const [openSignal, setOpenSignal] = useState<TrainingSignal | null>(null);
  const imageFailed = imageSrc != null && imageSrc === failedImageSrc;
  const canOpenDeformation = volcano.deformation.sample != null;
  const canOpenSeismic = volcano.seismic.sample != null;

  return (
    <div data-testid={TEST_IDS.volcanoPopup} className="min-w-0">
      {imageSrc && !imageFailed ? (
        <Image
          src={imageSrc}
          alt={volcano.name}
          width={256}
          height={128}
          sizes="256px"
          quality={32}
          className="mb-2 h-32 w-64 object-cover"
          onError={() => setFailedImageSrc(imageSrc)}
        />
      ) : (
        <Image
          src={IMAGE_LOADING}
          alt={volcano.name}
          width={256}
          height={256}
          sizes="256px"
          quality={16}
          className="mb-2 h-48 w-64 object-contain"
        />
      )}
      <div className="flex items-center gap-2 flex-wrap">
        <p
          className={`font-bold text-zinc-900 truncate ${isMobile ? "text-sm" : "text-base"}`}
        >
          {volcano.name}
        </p>
      </div>
      <div
        className={`mt-0.5 flex flex-wrap items-center gap-x-1.5 gap-y-1 text-zinc-600 ${metaText}`}
      >
        <span className={`${chipClass} border-zinc-300 text-zinc-600`}>
          {volcano.country.toUpperCase()}
        </span>
        <span className={`${chipClass} border-zinc-300 text-zinc-600`}>
          {volcano.zone.toUpperCase()}
        </span>
        {volcano.gvpNumber ? (
          <span className={`${chipClass} border-zinc-300 text-zinc-600`}>
            #{formatNumber(volcano.gvpNumber)}
          </span>
        ) : null}
        {volcano.volcanicClass ? (
          <span className={`${chipClass} border-zinc-300 text-zinc-600`}>
            {volcano.volcanicClass.toUpperCase()}
          </span>
        ) : null}
        <span className={`${chipClass} border-zinc-200 text-zinc-600`}>
          Latitude: {formatDecimal(volcano.latitude)}
        </span>
        <span className={`${chipClass} border-zinc-200 text-zinc-600`}>
          Longitude: {formatDecimal(volcano.longitude)}
        </span>
        <span className={`${chipClass} border-zinc-200 text-zinc-600`}>
          Elevation: {volcano.elevationM} m
        </span>
        <Dot />
        {canOpenDeformation ? (
          <button
            type="button"
            data-testid={TEST_IDS.inferenceDeformationButton}
            onClick={(event) => {
              event.stopPropagation();
              setOpenSignal(TrainingSignal.deformation);
            }}
            className={`${chipClass} font-semibold border-zinc-300 text-zinc-800 hover:bg-zinc-100`}
          >
            Click to see {signalLabel.deformation}!
          </button>
        ) : null}
        <Dot />
        {canOpenSeismic ? (
          <button
            type="button"
            data-testid={TEST_IDS.inferenceSeismicButton}
            onClick={(event) => {
              event.stopPropagation();
              setOpenSignal(TrainingSignal.seismic);
            }}
            className={`${chipClass} font-semibold border-zinc-300 text-zinc-800 hover:bg-zinc-100`}
          >
            Click to see {signalLabel.seismic}!
          </button>
        ) : null}
      </div>
      {openSignal != null ? (
        <HomeInference
          key={`${volcano.id}:${openSignal}`}
          userId={userId}
          volcano={volcano}
          signal={openSignal}
          onClose={() => setOpenSignal(null)}
        />
      ) : null}
    </div>
  );
}
