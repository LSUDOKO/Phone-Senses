import React from "react";
import { AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C } from "./brand";
import { Film, musicVolume } from "./Film";
import vo from "./data/vo.json";

/** Ranges of the master film (seconds) that make the <90 s hackathon cut, in order. */
const RANGES: [number, number][] = [
  [0, 17.5], // cold open + title
  [50, 57.6], // the fix: Phone Senses, a Hermes plugin
  [65.6, 68.5], // here's his real day
  [70, 79.1], // morning brief, scam on top
  [101.6, 126.0], // scam check, text Mom (allow), deny
  [133.9, 143.0], // phone under the bed: ring + webcam
  [186, 201], // outro
];
const FADE = 5; // frames of dip at each join

const LINES = vo.sections.flatMap((s) => s.lines);
let acc = 0;
const PLACED = RANGES.map(([a, b]) => {
  const at = acc;
  acc += b - a;
  return { a, b, at };
});
export const CUT_SECONDS = acc + 1;
/** VO lines remapped onto the cut's timeline, for music ducking. */
const CUT_LINES = PLACED.flatMap(({ a, b, at }) =>
  LINES.filter((l) => l.start >= a - 0.01 && l.end <= b + 0.01).map((l) => ({ start: l.start - a + at, end: l.end - a + at })),
);

const Dip: React.FC<{ dur: number; first: boolean; last: boolean }> = ({ dur, first, last }) => {
  const frame = useCurrentFrame();
  const o = Math.min(first ? 1 : interpolate(frame, [0, FADE], [0, 1], { extrapolateRight: "clamp" }), last ? 1 : interpolate(frame, [dur - FADE, dur], [1, 0], { extrapolateLeft: "clamp" }));
  return <AbsoluteFill style={{ backgroundColor: C.ink, opacity: 1 - o }} />;
};

export const Cut: React.FC = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: C.ink }}>
      {PLACED.map(({ a, b, at }, i) => {
        const dur = Math.round((b - a) * fps) + (i === PLACED.length - 1 ? fps : 0);
        return (
          <Sequence key={i} name={`${a}-${b}`} from={Math.round(at * fps)} durationInFrames={dur}>
            <Sequence from={-Math.round(a * fps)} layout="none">
              <Film music={false} />
            </Sequence>
            <Dip dur={dur} first={i === 0} last={i === PLACED.length - 1} />
          </Sequence>
        );
      })}
      <Audio src={staticFile("audio/music.mp3")} volume={(f) => musicVolume(f / fps, CUT_LINES, CUT_SECONDS - 1)} />
    </AbsoluteFill>
  );
};
