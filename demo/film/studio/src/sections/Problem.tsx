import React from "react";
import { AbsoluteFill, interpolate, random, useCurrentFrame } from "remotion";
import { C, EASE_IN, EXPO, Kinetic } from "../brand";
import {
  clamp,
  Counter,
  display,
  Drift,
  FilmField,
  Icon,
  IconName,
  mono,
  NotifCard,
  Reveal,
  SourceLine,
  Tag,
  useCues,
  useInOut,
  useShake,
} from "../motion";
import { DESK, DeskLine, LaptopOutline, PhoneOutline } from "../motion/desk";

const ID = "problem";
const LEFT = 150;

/** Phone outline on the right for the intro beats; glyphs rain into it; then a zoom-through. */
const IntroPhone: React.FC<{ rainAt: number; zoomAt: number }> = ({
  rainAt,
  zoomAt,
}) => {
  const frame = useCurrentFrame();
  const glyphs: IconName[] = [
    "rupee",
    "parcel",
    "call",
    "bell",
    "sms",
    "mail",
    "cal",
    "card",
    "chat",
    "rupee",
    "battery",
    "sms",
    "call",
    "parcel",
  ];
  const landed = glyphs.filter((_, i) => frame >= rainAt + i * 4 + 12).length;
  const zoom = interpolate(frame, [zoomAt, zoomAt + 21], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const { enter } = useInOut(6, undefined, 18);
  const buzz = useShake(40, 52, 3, "buzz");
  const { x, y, w, h } = DESK.phone;
  return (
    <AbsoluteFill
      style={{
        opacity: enter * (1 - interpolate(zoom, [0.55, 0.9], [0, 1], clamp)),
        scale: `${1 + zoom * 7}`,
        transformOrigin: `${x + w / 2}px ${y + h / 2}px`,
        translate: frame < rainAt ? buzz : `${(1 - enter) * 60}px 0`,
      }}
    >
      <PhoneOutline glow={Math.min(1, landed / glyphs.length + zoom)} />
      {glyphs.map((g, i) => {
        const at = rainAt + i * 4;
        const p = interpolate(frame, [at, at + 14], [0, 1], {
          ...clamp,
          easing: EXPO,
        });
        if (p <= 0 || p >= 1) return null;
        const gx = x + w / 2 + (random(`gx${i}`) - 0.5) * 220;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: gx - 42,
              top: interpolate(p, [0, 1], [-140, y + h / 2 - 42]),
              opacity: p < 0.85 ? 1 : (1 - p) / 0.15,
              color: C.paper,
            }}
          >
            <Icon name={g} size={84} stroke={1.6} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/** Bank-SMS chips streaming up the right side (amounts masked). */
const SmsStream: React.FC<{ at: number; out: number }> = ({ at, out }) => {
  const frame = useCurrentFrame();
  const { v } = useInOut(at, out, 12, 8);
  const scroll = (frame - at) * 7;
  return (
    <div
      style={{
        position: "absolute",
        left: 1180,
        top: 120,
        width: 600,
        height: 760,
        overflow: "hidden",
        opacity: v,
        WebkitMaskImage:
          "linear-gradient(180deg, transparent 0%, #000 18%, #000 82%, transparent 100%)",
        maskImage:
          "linear-gradient(180deg, transparent 0%, #000 18%, #000 82%, transparent 100%)",
      }}
    >
      {Array.from({ length: 16 }).map((_, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: 20,
            top: ((((i * 104 - scroll) % 1664) + 1664) % 1664) - 104,
          }}
        >
          <NotifCard
            width={540}
            scale={0.82}
            n={{
              app: "Messages",
              icon: "sms",
              title: i % 3 === 1 ? "VM-BANKIN" : "AX-BANKIN",
              body:
                i % 4 === 2
                  ? "Rs ••• credited by UPI · Ref •••••"
                  : "Rs ••• debited via UPI · Ref •••••",
              time: `${i + 1}m`,
            }}
          />
        </div>
      ))}
    </div>
  );
};

/** 13 grey scam bubbles stacking with a posterised 1 px jitter; they collapse into the ₹ at the end. */
const ScamBubbles: React.FC<{ at: number; collapseAt: number }> = ({
  at,
  collapseAt,
}) => {
  const frame = useCurrentFrame();
  const channels: [IconName, string][] = [
    ["sms", "Text"],
    ["mail", "Email"],
    ["chat", "Social"],
  ];
  const col = interpolate(frame, [collapseAt, collapseAt + 12], [0, 1], {
    ...clamp,
    easing: EASE_IN,
  });
  const jf = Math.floor(frame / 2.5); // ~12 fps jitter
  return (
    <>
      {Array.from({ length: 13 }).map((_, i) => {
        const p = interpolate(frame, [at + i * 2, at + i * 2 + 10], [0, 1], {
          ...clamp,
          easing: EXPO,
        });
        const [icon, label] = channels[i % 3];
        const bx = 1180;
        const by = 196 + i * 54;
        const jx = (random(`jx${i}${jf}`) - 0.5) * 2;
        const jy = (random(`jy${i}${jf}`) - 0.5) * 2;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: bx,
              top: by,
              width: 560,
              height: 44,
              borderRadius: 22,
              background: "rgba(120,124,140,.22)",
              border: "1px solid rgba(255,255,255,.1)",
              display: "flex",
              alignItems: "center",
              gap: 14,
              padding: "0 18px",
              color: C.mist,
              opacity: p * (1 - col),
              translate: `${jx + (1 - p) * 40 + col * (960 - bx - 280)}px ${jy + col * (540 - by - 22)}px`,
              scale: `${1 - col * 0.9}`,
            }}
          >
            <Icon name={icon} size={22} />
            <div
              style={{
                height: 8,
                width: 140 + random(`bw${i}`) * 180,
                borderRadius: 4,
                background: "rgba(241,241,238,.28)",
              }}
            />
            <div
              style={{
                height: 8,
                width: 40 + random(`bv${i}`) * 60,
                borderRadius: 4,
                background: "rgba(241,241,238,.14)",
              }}
            />
            <span style={{ marginLeft: "auto", ...mono(13) }}>{label}</span>
          </div>
        );
      })}
    </>
  );
};

/** Laptop and phone a foot apart; the dashed link draws on, then snaps. */
const Desk: React.FC<{ at: number; drawAt: number; snapAt: number }> = ({
  at,
  drawAt,
  snapAt,
}) => {
  const frame = useCurrentFrame();
  const { enter } = useInOut(at, undefined, 16);
  const draw = interpolate(frame, [drawAt, drawAt + 15], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const brk = interpolate(frame, [snapAt, snapAt + 10], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  const shake = useShake(snapAt, snapAt + 6, 5, "snap");
  const mid = (DESK.lineA + DESK.lineB) / 2;
  return (
    <AbsoluteFill style={{ opacity: enter, translate: shake }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          translate: `${(1 - enter) * -50}px 0`,
        }}
      >
        <LaptopOutline cursorOn={frame < 930 && Math.floor(frame / 9) % 2 === 0} />
      </div>
      <div
        style={{
          position: "absolute",
          inset: 0,
          translate: `${(1 - enter) * 50}px 0`,
        }}
      >
        <PhoneOutline />
      </div>
      <DeskLine id="problem" draw={draw} brk={brk} />
      <Tag
        at={drawAt + 8}
        out={snapAt - 2}
        style={{
          left: mid - 200,
          width: 400,
          top: DESK.lineY - 50,
          textAlign: "center",
          color: C.mist,
        }}
      >
        ≈ 30 cm · one foot
      </Tag>
      <Tag
        at={at + 10}
        out={938}
        style={{
          left: DESK.laptop.x,
          width: DESK.laptop.w,
          top: DESK.laptop.y + DESK.laptop.h + 56,
          textAlign: "center",
          color: C.mist,
        }}
      >
        Hermes · laptop
      </Tag>
      <Tag
        at={at + 14}
        out={938}
        style={{
          left: DESK.phone.x - 50,
          width: DESK.phone.w + 100,
          top: DESK.phone.y + DESK.phone.h + 24,
          textAlign: "center",
          color: C.mist,
        }}
      >
        His phone
      </Tag>
    </AbsoluteFill>
  );
};

export const Problem: React.FC = () => {
  const frame = useCurrentFrame();
  const cue = useCues(ID);
  const p1 = cue("p1");
  const p2 = cue("p2");
  const p3 = cue("p3");
  const p4 = cue("p4");
  const p5 = cue("p5");
  const p6 = cue("p6");
  const p7 = cue("p7");
  const p8 = cue("p8");
  const statOut = p5.s - 10;
  const scamOut = p6.s - 4;
  const fraudOut = p7.s - 12;
  return (
    <AbsoluteFill style={{ backgroundColor: C.ink }}>
      <FilmField sectionId={ID} intensity={0.6} />

      {/* A · Meet Arpit */}
      <div style={{ position: "absolute", left: LEFT, top: 330 }}>
        <Kinetic
          text="Meet Arpit."
          start={p1.s + 4}
          stagger={3}
          size={160}
          align="left"
          exitAt={p2.s - 12}
        />
      </div>
      <Tag
        at={p1.s + 18}
        out={p2.s - 12}
        style={{ left: LEFT + 6, top: 540, fontSize: 18 }}
      >
        Arpit · final-year student · Hamirpur, HP
      </Tag>
      <Tag
        at={p1.s + 26}
        out={p2.s - 12}
        style={{ left: LEFT + 6, top: 576, fontSize: 16, color: C.mist }}
      >
        Himachal Pradesh · exam week
      </Tag>

      {/* B · It all lands here */}
      <div style={{ position: "absolute", left: LEFT, top: 380 }}>
        <Kinetic
          text="It all lands here."
          start={p2.s}
          stagger={2}
          size={120}
          align="left"
          maxWidth={1050}
          exitAt={p3.s - 10}
        />
      </div>
      <IntroPhone rainAt={p2.s + 6} zoomAt={p3.s - 10} />

      {/* C · UPI volume, then his bank's texts */}
      <Drift from={p3.s} to={p5.s}>
        <div
          style={{
            position: "absolute",
            left: LEFT,
            top: 330,
            transformOrigin: "0 50%",
            scale: `${interpolate(frame, [p4.s - 6, p4.s + 10], [1, 0.72], { ...clamp, easing: EXPO })}`,
          }}
        >
          <Reveal at={p3.s + 2} out={statOut}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 28 }}>
              <Counter
                to={25.47}
                decimals={2}
                at={p3.s + 2}
                style={display(240)}
              />
              <span style={display(110)}>billion</span>
            </div>
          </Reveal>
          <Reveal at={p3.s + 8} out={statOut} rise={20}>
            <div
              style={{
                ...display(46, {
                  fontWeight: 600,
                  fontStretch: "110%",
                  letterSpacing: "-0.01em",
                  color: "rgba(241,241,238,.75)",
                }),
                marginTop: 26,
              }}
            >
              UPI payments in India · October 2026
            </div>
          </Reveal>
        </div>
        <SmsStream at={p4.s - 4} out={statOut} />
      </Drift>
      <Tag
        at={p4.s + 2}
        out={statOut}
        style={{ right: 96, top: 64, textAlign: "right" }}
      >
        His bank · one text per payment
      </Tag>
      <SourceLine at={p3.s + 12} out={statOut}>
        25,466.70 million UPI transactions · October 2026 · NPCI, UPI Product
        Statistics · npci.org.in
      </SourceLine>

      {/* D · 13 scam messages */}
      <Drift from={p5.s} to={p6.s}>
        <div style={{ position: "absolute", left: LEFT, top: 250 }}>
          <Reveal at={p5.s} out={scamOut}>
            <Counter
              to={13}
              at={p5.s}
              style={display(330, { lineHeight: 0.82 })}
            />
          </Reveal>
          <div style={{ marginTop: 40 }}>
            <Kinetic
              text="scam messages a day."
              start={p5.s + 6}
              stagger={2}
              size={96}
              align="left"
              maxWidth={900}
              exitAt={scamOut}
            />
          </div>
        </div>
        <ScamBubbles at={p5.s + 4} collapseAt={p6.s - 12} />
      </Drift>
      <SourceLine at={p5.s + 10} out={scamOut}>
        13 scam messages a day, on average in India, across text, email &amp;
        social · McAfee, 2026 State of the Scamiverse
      </SourceLine>

      {/* E · ₹55,050 crore */}
      <Drift from={p6.s} to={p7.s} amount={0.05}>
        <AbsoluteFill
          style={{
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            gap: 30,
            translate: "0 -40px",
          }}
        >
          <Reveal at={p6.s} out={fraudOut} rise={0}>
            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: 26,
                scale: `${interpolate(frame, [p6.s, p6.s + 14], [0.6, 1], { ...clamp, easing: EXPO })}`,
              }}
            >
              <Counter to={55050} prefix="₹" at={p6.s} style={display(220)} />
              <span style={display(100)}>crore+</span>
            </div>
          </Reveal>
          <Reveal at={p6.s + 30} out={fraudOut} rise={20}>
            <div
              style={display(46, {
                fontWeight: 600,
                fontStretch: "110%",
                letterSpacing: "-0.01em",
                color: "rgba(241,241,238,.75)",
              })}
            >
              reported in cyber fraud since 2021
            </div>
          </Reveal>
        </AbsoluteFill>
      </Drift>
      <SourceLine at={p6.s + 20} out={fraudOut}>
        ₹55,050 crore reported in cyber fraud since 2021 · 65.9 lakh+
        financial-fraud complaints, 2021–2025 · MHA / I4C reply, PIB, 21 Jul
        2026
      </SourceLine>

      {/* F · laptop and phone, a foot apart, and the link snaps */}
      <Desk at={p7.s - 6} drawAt={p7.s + 30} snapAt={p8.s + 4} />
      <AbsoluteFill style={{ alignItems: "center", paddingTop: 120 }}>
        <Kinetic
          text="It can't see any of it."
          start={p8.s}
          stagger={2}
          size={100}
          maxWidth={1728}
          exitAt={944}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
