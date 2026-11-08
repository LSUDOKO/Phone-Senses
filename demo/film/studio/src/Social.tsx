import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C, Field, Grain, Mark, MONO } from "./brand";
import { Dip, place } from "./Cut";
import { Captions, Film, musicVolume } from "./Film";
import beats from "./data/beats.json";

/** 9:16 social cut (~54 s): the hook, the brief, scam + text Mom, find my phone, the name. */
const RANGES: [number, number][] = [
  [0, 17.5],
  [70, 79.1],
  [101.6, 117.0],
  [133.9, 143.0],
  [186, 189.2],
];
// walkthrough crops in to the terminal window so its text stays readable on a phone
// (window: x 110, 1106 wide with the phone beside it; centered and 1306 wide without)
const CROP = (t: number) => {
  if (t < 70 || t >= 146) return { x: 0, w: 1920 };
  const b = beats.beats.find((x) => t >= x.start && t < x.start + x.duration);
  return b && !b.phone ? { x: 290, w: 1340 } : { x: 96, w: 1140 };
};
const TOP = 300;
const S = place(RANGES);
export const SOCIAL_SECONDS = S.seconds;

const CAPTION_TOP = TOP + 1080 * (1080 / 1140) + 30;

/** One range of the film, cropped per frame to the region worth reading. */
const Cropped: React.FC<{ a: number; dur: number; first: boolean; last: boolean }> = ({ a, dur, first, last }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const crop = CROP(a + frame / fps);
  const k = 1080 / crop.w;
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        top: TOP + (1080 * (1080 / 1140) - 1080 * k) / 2,
        width: 1080,
        height: 1080 * k,
        overflow: "hidden",
        borderRadius: 28,
        boxShadow: "0 40px 120px rgba(0,0,0,.6), 0 0 0 2px rgba(255,255,255,.1)",
      }}
    >
      <div style={{ position: "absolute", left: -crop.x * k, top: 0, width: 1920, height: 1080, scale: `${k}`, transformOrigin: "0 0" }}>
        <Sequence from={-Math.round(a * fps)} layout="none">
          <Film music={false} captions={false} />
        </Sequence>
        <Dip dur={dur} first={first} last={last} />
      </div>
    </div>
  );
};

export const Social: React.FC = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: C.ink }}>
      <Field intensity={0.9} />
      <div style={{ position: "absolute", top: 150, left: 0, right: 0, display: "flex", justifyContent: "center", alignItems: "center", gap: 18 }}>
        <Mark size={64} start={-100} />
        <div style={{ fontFamily: MONO, fontSize: 26, letterSpacing: "0.12em", color: C.mist }}>PHONE SENSES · FOR HERMES AGENT</div>
      </div>
      {S.placed.map(({ a, b, at }, i) => {
        const dur = Math.round((b - a) * fps) + (i === S.placed.length - 1 ? fps : 0);
        return (
          <Sequence key={i} name={`${a}-${b}`} from={Math.round(at * fps)} durationInFrames={dur}>
            <Cropped a={a} dur={dur} first={i === 0} last={i === S.placed.length - 1} />
            <div style={{ position: "absolute", left: 0, right: 0, top: CAPTION_TOP, height: 1920 - 260 - CAPTION_TOP }}>
              <Sequence from={-Math.round(a * fps)} layout="none">
                <Captions big />
              </Sequence>
            </div>
          </Sequence>
        );
      })}
      <div style={{ position: "absolute", bottom: 150, left: 0, right: 0, textAlign: "center", fontFamily: MONO, fontSize: 28, letterSpacing: "0.08em", color: C.blueText }}>
        phone-senses.pages.dev
      </div>
      <Grain opacity={0.1} />
      <Audio src={staticFile("audio/music.mp3")} volume={(f) => musicVolume(f / fps, S.lines, S.seconds - 1)} />
    </AbsoluteFill>
  );
};
