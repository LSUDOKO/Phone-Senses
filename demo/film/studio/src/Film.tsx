import React from "react";
import { AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C, DISPLAY } from "./brand";
import { sectionFrames, sectionStartFrame } from "./motion";
import { SECTIONS } from "./sections";
import { Walkthrough } from "./sections/Walkthrough";
import beats from "./data/beats.json";
import captions from "./data/captions.json";
import vo from "./data/vo.json";

const ALL: Record<string, React.FC> = { ...SECTIONS, walk: Walkthrough };
const LINES = vo.sections.flatMap((s) => s.lines);
const END_CARD_AT = LINES.find((l) => l.id === "o3")!.start - 0.1;
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const filmDuration = (fps: number) => Math.round(vo.duration * fps) + fps; // 1 s tail after the last word

/** Music under the voice: 0 → full between lines, ducked under speech, fades in/out at the ends. */
export const musicVolume = (t: number, lines: { start: number; end: number }[] = LINES, total = vo.duration) => {
  let duck = 0;
  for (const l of lines) {
    const d = Math.min(t - (l.start - 0.25), l.end + 0.35 - t);
    if (d > 0) duck = Math.max(duck, Math.min(1, d / 0.25));
  }
  const ends = interpolate(t, [0, 1.5, total - 2, total + 1], [0, 1, 1, 0], clamp);
  return (0.34 - 0.24 * duck) * ends;
};

/** Burned-in captions: one short page at a time, the spoken word lit in ultramarine tint. */
const Captions: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  // the end card spells out the last lines, and its small print sits where captions go
  if (t >= END_CARD_AT) return null;
  const pages = captions.pages;
  const i = pages.findIndex((p, k) => t >= p.start - 0.05 && t < Math.min(p.end + 0.4, pages[k + 1]?.start ?? Infinity));
  if (i < 0) return null;
  const page = pages[i];
  const pop = interpolate(t, [page.start - 0.05, page.start + 0.12], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 46, pointerEvents: "none" }}>
      <div
        style={{
          padding: "10px 22px",
          borderRadius: 16,
          background: "rgba(5,5,7,.62)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(255,255,255,.08)",
          fontFamily: DISPLAY,
          fontWeight: 650,
          fontStretch: "104%",
          fontSize: 40,
          letterSpacing: "-0.01em",
          color: C.paper,
          opacity: pop,
          translate: `0 ${(1 - pop) * 8}px`,
        }}
      >
        {page.words.map((w, k) => (
          <span key={k} style={{ color: t >= w.start && t < w.end + 0.08 ? C.blueText : C.paper }}>
            {w.text}
            {k < page.words.length - 1 ? " " : ""}
          </span>
        ))}
      </div>
    </AbsoluteFill>
  );
};

type Sfx = { at: number; src: string; vol: number };

const sfxCues = (): Sfx[] => {
  const cues: Sfx[] = [{ at: 0.05, src: "ping", vol: 0.5 }];
  const title = vo.sections.find((s) => s.id === "title")!;
  cues.push({ at: title.start, src: "hit", vol: 0.8 });
  for (const s of vo.sections.slice(2)) cues.push({ at: s.start - 0.35, src: "whoosh", vol: 0.35 });
  // the real keypresses on the approval prompt
  for (const b of beats.beats) {
    const panel = b.pieces.find((p) => p.mark === "panel");
    if (!panel) continue;
    const press = b.id.startsWith("b07") ? panel.t0 + panel.out : panel.t0 + panel.out - 0.39;
    cues.push({ at: b.start + press, src: "click", vol: 0.7 });
  }
  return cues;
};

export const Film: React.FC<{ music?: boolean }> = ({ music = true }) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: C.ink }}>
      {vo.sections.map((s) => {
        const Comp = ALL[s.id];
        return Comp ? (
          <Sequence key={s.id} name={s.id} from={sectionStartFrame(s.id, fps)} durationInFrames={sectionFrames(s.id, fps) + (s.id === "outro" ? fps : 0)}>
            <Comp />
          </Sequence>
        ) : null;
      })}
      <Captions />
      {music ? <Audio src={staticFile("audio/music.mp3")} volume={(f) => musicVolume(f / fps)} /> : null}
      {LINES.map((l) => (
        <Sequence key={l.id} name={`vo ${l.id}`} from={Math.round(l.start * fps)} layout="none">
          <Audio src={staticFile(`audio/vo/${l.id}.wav`)} />
        </Sequence>
      ))}
      {sfxCues().map((c, k) => (
        <Sequence key={k} from={Math.max(0, Math.round(c.at * fps))} durationInFrames={Math.round(1.5 * fps)} layout="none">
          <Audio src={staticFile(`audio/sfx/${c.src}.wav`)} volume={c.vol} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
