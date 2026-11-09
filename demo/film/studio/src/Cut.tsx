import React from "react";
import { AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C } from "./brand";
import { Film, musicVolume } from "./Film";
import vo from "./data/vo.json";

/** Ranges of the master film (seconds) that make the <90 s hackathon cut, in order. */
/** Look up a voice line or section on the film timeline (seconds), so ranges follow the voice-over. */
export const L = (id: string) => vo.sections.flatMap((s) => s.lines).find((l) => l.id === id)!;
export const SEC = (id: string) => vo.sections.find((s) => s.id === id)!;

/** Ranges of the master film (seconds) that make the <90 s hackathon cut, in order. */
const RANGES: [number, number][] = [
  [0, SEC("title").end - 0.5], // cold open + title
  [L("k1").start, L("k2").end + 0.6], // the fix: Phone Senses, a Hermes plugin
  [L("w1").start, L("w3").start - 0.15], // morning brief, scam on top
  [L("w8").start - 0.15, L("w12").start - 0.1], // text Mom (allow), deny, scam tripwire on the real phone
  [SEC("outro").start, SEC("outro").end], // outro
];
export const FADE = 5; // frames of dip at each join

const LINES = vo.sections.flatMap((s) => s.lines);

/** Lay ranges end to end; returns placements, total seconds and the VO lines on the new timeline. */
export const place = (ranges: [number, number][]) => {
  let acc = 0;
  const placed = ranges.map(([a, b]) => {
    const at = acc;
    acc += b - a;
    return { a, b, at };
  });
  const lines = placed.flatMap(({ a, b, at }) =>
    LINES.filter((l) => l.start >= a - 0.01 && l.end <= b + 0.01).map((l) => ({ start: l.start - a + at, end: l.end - a + at })),
  );
  return { placed, seconds: acc + 1, lines };
};

const CUT = place(RANGES);
const PLACED = CUT.placed;
export const CUT_SECONDS = CUT.seconds;
const CUT_LINES = CUT.lines;

export const Dip: React.FC<{ dur: number; first: boolean; last: boolean }> = ({ dur, first, last }) => {
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
