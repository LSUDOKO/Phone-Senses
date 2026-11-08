import React from "react";
import { C, MONO } from "../brand";

/** Shared geometry so Problem's last frame and Turn's first frame match exactly. */
export const DESK = {
  phone: { x: 1300, y: 250, w: 290, h: 580 },
  laptop: { x: 230, y: 330, w: 620, h: 390 },
  lineY: 540,
  lineA: 880, // laptop edge
  lineB: 1270, // phone edge
};

const stroke = "rgba(241,241,238,.55)";

/** Outline phone with a stack of notification bars on the screen. */
export const PhoneOutline: React.FC<{
  glow?: number;
  bars?: number;
  style?: React.CSSProperties;
}> = ({ glow = 0, bars = 6, style }) => {
  const { x, y, w, h } = DESK.phone;
  return (
    <svg
      width={1920}
      height={1080}
      style={{
        position: "absolute",
        left: 0,
        top: 0,
        overflow: "visible",
        ...style,
      }}
    >
      <rect
        x={x}
        y={y}
        width={w}
        height={h}
        rx={44}
        fill="rgba(10,10,16,.65)"
        stroke={stroke}
        strokeWidth={2}
      />
      <rect
        x={x + 12}
        y={y + 12}
        width={w - 24}
        height={h - 24}
        rx={34}
        fill={`rgba(31,43,255,${0.05 + glow * 0.22})`}
        stroke="rgba(241,241,238,.12)"
        style={{
          filter:
            glow > 0
              ? `drop-shadow(0 0 ${30 * glow}px rgba(31,43,255,${0.6 * glow}))`
              : undefined,
        }}
      />
      <rect
        x={x + w / 2 - 30}
        y={y + 26}
        width={60}
        height={8}
        rx={4}
        fill="rgba(241,241,238,.25)"
      />
      {Array.from({ length: bars }).map((_, i) => (
        <g key={i} opacity={0.85 - i * 0.1}>
          <rect
            x={x + 30}
            y={y + 70 + i * 70}
            width={w - 60}
            height={54}
            rx={14}
            fill="rgba(241,241,238,.08)"
            stroke="rgba(241,241,238,.14)"
          />
          <rect
            x={x + 44}
            y={y + 84 + i * 70}
            width={26}
            height={26}
            rx={7}
            fill="rgba(241,241,238,.22)"
          />
          <rect
            x={x + 82}
            y={y + 86 + i * 70}
            width={110 - (i % 3) * 18}
            height={8}
            rx={4}
            fill="rgba(241,241,238,.4)"
          />
          <rect
            x={x + 82}
            y={y + 100 + i * 70}
            width={150 - (i % 2) * 40}
            height={7}
            rx={3.5}
            fill="rgba(241,241,238,.2)"
          />
        </g>
      ))}
    </svg>
  );
};

/** Outline laptop with an idle Hermes prompt. */
export const LaptopOutline: React.FC<{
  cursorOn?: boolean;
  style?: React.CSSProperties;
}> = ({ cursorOn = true, style }) => {
  const { x, y, w, h } = DESK.laptop;
  return (
    <svg
      width={1920}
      height={1080}
      style={{
        position: "absolute",
        left: 0,
        top: 0,
        overflow: "visible",
        ...style,
      }}
    >
      <rect
        x={x}
        y={y}
        width={w}
        height={h}
        rx={18}
        fill="rgba(10,10,16,.65)"
        stroke={stroke}
        strokeWidth={2}
      />
      <rect
        x={x + 14}
        y={y + 14}
        width={w - 28}
        height={h - 28}
        rx={8}
        fill="rgba(255,255,255,.02)"
        stroke="rgba(241,241,238,.1)"
      />
      <path
        d={`M${x - 50} ${y + h + 6} L${x + w + 50} ${y + h + 6} L${x + w + 20} ${y + h + 34} L${x - 20} ${y + h + 34} Z`}
        fill="rgba(10,10,16,.65)"
        stroke={stroke}
        strokeWidth={2}
        strokeLinejoin="round"
      />
      <text x={x + 44} y={y + 74} fontFamily={MONO} fontSize={24} fill={C.mist}>
        hermes &gt; <tspan opacity={cursorOn ? 1 : 0}>▌</tspan>
      </text>
      {[0, 1, 2].map((i) => (
        <rect
          key={i}
          x={x + 44}
          y={y + 110 + i * 34}
          width={[300, 220, 260][i]}
          height={10}
          rx={5}
          fill="rgba(241,241,238,.08)"
        />
      ))}
    </svg>
  );
};

/**
 * The link between laptop and phone.
 * draw: 0..1 draw-on, brk: 0..1 snap + sag, fuse: 0..1 halves rejoin in ultramarine, sweep: 0..1 light along the line.
 */
export const DeskLine: React.FC<{
  id: string;
  draw: number;
  brk?: number;
  fuse?: number;
  sweep?: number;
}> = ({ id, draw, brk = 0, fuse = 0, sweep = -1 }) => {
  const { lineA: a, lineB: b, lineY: y } = DESK;
  const mid = (a + b) / 2;
  const open = brk * (1 - fuse); // how broken we are now
  const gap = 26 * open;
  const sag = 8 * open + 10 * open;
  const len = (b - a) * draw;
  const color =
    fuse > 0
      ? `rgb(${Math.round(154 - 123 * fuse)},${Math.round(160 - 117 * fuse)},${Math.round(180 + 75 * fuse)})`
      : C.mist;
  const dash = fuse > 0.6 ? undefined : "10 10";
  const w = 3 + fuse * 2;
  return (
    <svg
      width={1920}
      height={1080}
      style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}
    >
      <defs>
        <clipPath id={`deskline-${id}`}>
          <rect x={a - 10} y={y - 200} width={len + 10} height={400} />
        </clipPath>
      </defs>
      <g
        clipPath={`url(#deskline-${id})`}
        style={{
          filter:
            fuse > 0
              ? `drop-shadow(0 0 ${14 * fuse}px rgba(31,43,255,.9))`
              : undefined,
        }}
      >
        <line
          x1={a}
          y1={y}
          x2={mid - gap}
          y2={y + sag}
          stroke={color}
          strokeWidth={w}
          strokeDasharray={dash}
          strokeLinecap="round"
        />
        <line
          x1={mid + gap}
          y1={y + sag}
          x2={b}
          y2={y}
          stroke={color}
          strokeWidth={w}
          strokeDasharray={dash}
          strokeLinecap="round"
        />
        <circle cx={a} cy={y} r={6} fill={color} />
        <circle cx={b} cy={y} r={6} fill={color} />
      </g>
      {sweep >= 0 && sweep <= 1 ? (
        <circle
          cx={a + (b - a) * sweep}
          cy={y}
          r={9}
          fill="#fff"
          style={{
            filter:
              "drop-shadow(0 0 12px #1F2BFF) drop-shadow(0 0 30px #1F2BFF)",
          }}
        />
      ) : null}
    </svg>
  );
};
