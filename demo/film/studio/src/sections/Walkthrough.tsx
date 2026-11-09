import React from "react";
import { AbsoluteFill, Audio, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C, Callout, EASE_IN, EXPO, GlassWindow, PhoneFrame } from "../brand";
import { clamp, FilmField, mono } from "../motion";
import beats from "../data/beats.json";
import vo from "../data/vo.json";

const ID = "walk";
const WALK_START = vo.sections.find((s) => s.id === ID)!.start;
// Terminal render: 118x34 cells, 16x37 px, 28 px pad -> 1944x1314.
const SRC_W = 1944;
const SRC_H = 1314;
const PAD = 28;
const CELL_H = 37;
const WIN_TOP = 118;
const WIN_H = 800;
const CONTENT_H = WIN_H - 52;
const CONTENT_W = Math.round((CONTENT_H * SRC_W) / SRC_H);
const PHONE_H = 744;

type Beat = (typeof beats.beats)[number] & {
  zoom?: { row: number | null; rows: number; scale: number; from: number; to: number; anchor: string };
  callout?: { text: string; at: number };
};

/** Zoom toward a terminal row: scale from the left edge, slide the row to the middle, never show an edge. */
const useZoom = (b: Beat) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const z = b.zoom;
  if (!z || z.row === null) return { s: 1, t: 0, rowY: CONTENT_H / 2 };
  const k = CONTENT_H / SRC_H;
  const rowY = (PAD + (z.row - (z.anchor === "bottom" ? z.rows - 1 : (z.rows - 1) / 2)) * CELL_H + CELL_H / 2) * k;
  const inP = interpolate(frame, [z.from * fps, z.from * fps + 16], [0, 1], { ...clamp, easing: EXPO });
  const outP = z.to < b.duration - 0.05 ? interpolate(frame, [z.to * fps, z.to * fps + 10], [0, 1], { ...clamp, easing: EASE_IN }) : 0;
  const p = inP * (1 - outP);
  const s = 1 + (z.scale - 1) * p;
  const want = (CONTENT_H / 2 - rowY) * p;
  const t = Math.max(-(CONTENT_H - rowY) * (s - 1), Math.min(rowY * (s - 1), want));
  return { s, t, rowY };
};

/** "Sped up" chip while a stretch of real time is compressed, honest about the edit. */
const SpeedChip: React.FC<{ b: Beat }> = ({ b }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const piece = b.pieces.find((p) => p.b !== null && t >= p.t0 && t < p.t0 + p.out && (p.b - p.a) / p.out > 4);
  const label = b.labels.find((l) => t >= l.from - 0.1 && t < l.to + 0.5);
  if (!piece && !label) return null;
  const rate = piece ? Math.round((piece.b! - piece.a) / piece.out) : 0;
  return (
    <div
      style={{
        position: "absolute",
        right: 22,
        top: 18,
        padding: "8px 14px",
        borderRadius: 999,
        background: "rgba(31,43,255,.85)",
        boxShadow: "0 10px 30px rgba(31,43,255,.35), inset 0 1px 0 rgba(255,255,255,.3)",
        ...mono(15, { color: C.paper, letterSpacing: "0.1em" }),
      }}
    >
      ▸▸ {label ? label.text : `${rate}× real time`}
    </div>
  );
};

/** Privacy blur over parts of the phone screen. Boxes are [x, y, w, h, from?, to?] in phone pixels (720x1600) and beat seconds. */
const PhoneBlur: React.FC<{ boxes: number[][] }> = ({ boxes }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const k = PHONE_H / 1600;
  return (
    <>
      {boxes
        .filter(([, , , , from = 0, to = 1e6]) => t >= from && t < to)
        .map(([x, y, w, h], i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x * k,
              top: y * k,
              width: w * k,
              height: h * k,
              borderRadius: 12,
              backdropFilter: "blur(14px)",
              background: "rgba(20,22,40,.35)",
            }}
          />
        ))}
    </>
  );
};

/** The phone's own spoken warning: its real recorded voice, plus a speech bubble with the words. */
const PhoneSpeech: React.FC<{ id: string; at: number; dur: number; text: string; x: number; y: number }> = ({ id, at, dur, text, x, y }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const from = Math.round(at * fps);
  const len = Math.round(dur * fps);
  const p = interpolate(frame, [from, from + 10], [0, 1], { ...clamp, easing: EXPO });
  const out = interpolate(frame, [from + len, from + len + 12], [1, 0], clamp);
  const pulse = 0.5 + 0.5 * Math.sin((frame - from) / 3);
  return (
    <>
      <Sequence from={from} durationInFrames={len} layout="none">
        <Audio src={staticFile(`beats/${id}/speech.wav`)} volume={1} />
      </Sequence>
      <div
        style={{
          position: "absolute",
          left: x,
          top: y,
          width: 560,
          padding: "22px 26px",
          borderRadius: 22,
          background: "rgba(31,43,255,.94)",
          color: C.paper,
          boxShadow: "0 30px 90px rgba(31,43,255,.45), inset 0 1px 0 rgba(255,255,255,.35)",
          opacity: p * out,
          translate: `0 ${(1 - p) * 24}px`,
          scale: `${0.96 + 0.04 * p}`,
        }}
      >
        <div style={{ ...mono(15, { color: "rgba(241,241,238,.85)" }), display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
          <span style={{ display: "inline-flex", gap: 3, alignItems: "flex-end", height: 16 }}>
            {[0.5, 1, 0.7, 0.9].map((h, i) => (
              <span key={i} style={{ width: 4, borderRadius: 2, background: C.paper, height: 6 + 10 * h * (i % 2 ? pulse : 1 - pulse) }} />
            ))}
          </span>
          The phone says, out loud
        </div>
        <div style={{ fontFamily: "Archivo", fontWeight: 700, fontSize: 34, lineHeight: 1.15, letterSpacing: "-0.01em" }}>“{text}”</div>
      </div>
    </>
  );
};

const BeatView: React.FC<{ b: Beat; dur: number; first: boolean; last: boolean }> = ({ b, dur, first, last }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { s, t, rowY } = useZoom(b);
  // hard cuts between beats (the window stays put); fades only into and out of the walkthrough
  const fadeIn = first ? interpolate(frame, [0, 8], [0, 1], clamp) : 1;
  const fadeOut = last ? interpolate(frame, [dur - 8, dur], [1, 0], clamp) : 1;
  const hasPhone = b.phone;
  const winW = hasPhone ? CONTENT_W : CONTENT_W + 200;
  const winLeft = hasPhone ? 110 : (1920 - winW) / 2;
  const phoneLeft = winLeft + winW + Math.round((1920 - (winLeft + winW) - (PHONE_H * 0.45 + 24)) / 2);
  const webcamAt = b.webcam ? 3.3 * fps : 1e6;
  const cam = interpolate(frame, [webcamAt, webcamAt + 16], [0, 1], { ...clamp, easing: EXPO });
  const demo = b.tag.startsWith("DEMO");
  return (
    <AbsoluteFill style={{ opacity: fadeIn * fadeOut }}>
      <div style={{ position: "absolute", left: winLeft, top: WIN_TOP }}>
        <GlassWindow title={`hermes chat  ·  ${demo ? "mock phone" : "real session"}`} width={winW} height={WIN_H}>
          <div
            style={{
              position: "absolute",
              inset: 0,
              transformOrigin: `0px ${rowY}px`,
              transform: `translateY(${t}px) scale(${s})`,
            }}
          >
            <OffthreadVideo src={staticFile(`beats/${b.id}/term.mp4`)} muted style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "left top" }} />
          </div>
          <SpeedChip b={b} />
        </GlassWindow>
        {b.callout ? <Callout text={b.callout.text} x={Math.round(winW * 0.5)} y={52 + CONTENT_H / 2 + 46} start={Math.round(b.callout.at * fps)} /> : null}
      </div>
      {hasPhone ? (
        <div style={{ position: "absolute", left: phoneLeft, top: WIN_TOP + 6, opacity: 1 - cam * 0.85, scale: `${1 - cam * 0.04}` }}>
          <PhoneFrame height={PHONE_H} label={b.tag}>
            <OffthreadVideo src={staticFile(`beats/${b.id}/phone.mp4`)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            <PhoneBlur boxes={(b as { blur?: number[][] }).blur ?? []} />
          </PhoneFrame>
        </div>
      ) : (
        <div style={{ position: "absolute", left: winLeft, top: WIN_TOP + WIN_H + 22, ...mono(16, { color: demo ? C.warn : C.mist }) }}>{demo ? `${b.tag} · fixtures, not my real bills` : b.tag}</div>
      )}
      {(b as { speech?: { at: number; dur: number; text: string } }).speech ? (
        <PhoneSpeech id={b.id} {...(b as { speech: { at: number; dur: number; text: string } }).speech}
          x={winLeft + winW - 600} y={WIN_TOP + 400} />
      ) : null}
      {b.webcam ? (
        <Sequence from={Math.round(webcamAt)} layout="none">
          <div
            style={{
              position: "absolute",
              right: 70,
              top: WIN_TOP + 40,
              width: 860,
              height: 484,
              borderRadius: 26,
              overflow: "hidden",
              opacity: cam,
              translate: `${(1 - cam) * 80}px 0`,
              boxShadow: "0 40px 120px rgba(0,0,0,.7), 0 0 0 1px rgba(255,255,255,.16), 0 0 90px rgba(31,43,255,.3)",
            }}
          >
            <OffthreadVideo
              src={staticFile(`beats/${b.id}/webcam.mp4`)}
              startFrom={Math.round(webcamAt)}
              volume={(f) => interpolate(f, [0, 10, dur - webcamAt - 20, dur - webcamAt], [0, 0.9, 0.9, 0], clamp)}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
            <div style={{ position: "absolute", left: 20, bottom: 16, ...mono(15, { color: C.paper }) }}>● webcam · the phone under the bed</div>
          </div>
        </Sequence>
      ) : null}
    </AbsoluteFill>
  );
};

/** Walkthrough: real recordings, cut to the voice-over (beats come from cut_beats.py). */
export const Walkthrough: React.FC = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: C.ink }}>
      <FilmField sectionId={ID} intensity={0.55} />
      <div style={{ position: "absolute", left: 110, top: 64, ...mono(16) }}>
        <span style={{ color: C.blueText }}>04</span>&nbsp;&nbsp;A REAL DAY · REAL PHONE
      </div>
      {(beats.beats as Beat[]).map((b, i) => {
        const from = Math.round((b.start - WALK_START) * fps);
        const dur = Math.round(b.duration * fps);
        return (
          <Sequence key={b.id} name={b.id} from={from} durationInFrames={dur}>
            <BeatView b={b} dur={dur} first={i === 0} last={i === beats.beats.length - 1} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

