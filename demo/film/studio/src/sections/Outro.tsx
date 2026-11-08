import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { C, EXPO, Mark, Wordmark } from "../brand";
import {
  clamp,
  display,
  Drift,
  FilmField,
  Headline,
  mono,
  Reveal,
  useCues,
} from "../motion";

const ID = "outro";

/** Mark + wordmark; lifts to the top of the end card on o3. */
const Lockup: React.FC<{ liftAt: number }> = ({ liftAt }) => {
  const frame = useCurrentFrame();
  const lift = interpolate(frame, [liftAt, liftAt + 18], [0, 1], {
    ...clamp,
    easing: EXPO,
  });
  return (
    <AbsoluteFill
      style={{
        alignItems: "center",
        justifyContent: "center",
        translate: `0 ${-100 - lift * 150}px`,
        scale: `${1 - lift * 0.22}`,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 40,
          whiteSpace: "nowrap",
        }}
      >
        <Mark size={180} start={0} />
        <Wordmark size={136} start={12} />
      </div>
    </AbsoluteFill>
  );
};

/** github line pulses ultramarine once on "Link below". */
const Link: React.FC<{ pulseAt?: number; children: React.ReactNode }> = ({
  pulseAt,
  children,
}) => {
  const frame = useCurrentFrame();
  const p =
    pulseAt === undefined
      ? 0
      : interpolate(
          frame,
          [pulseAt, pulseAt + 6, pulseAt + 28],
          [0, 1, 0],
          clamp,
        );
  return (
    <div
      style={{
        ...display(46, {
          fontWeight: 700,
          fontStretch: "108%",
          letterSpacing: "-0.015em",
        }),
        padding: "8px 22px",
        borderRadius: 14,
        background: `rgba(31,43,255,${0.85 * p})`,
        boxShadow: `0 0 ${50 * p}px rgba(31,43,255,${0.6 * p})`,
      }}
    >
      {children}
    </div>
  );
};

export const Outro: React.FC = () => {
  const cue = useCues(ID);
  const o1 = cue("o1");
  const o2 = cue("o2");
  const o3 = cue("o3");
  const o4 = cue("o4");
  const card = o3.s - 6;
  return (
    <AbsoluteFill style={{ backgroundColor: C.ink }}>
      <FilmField sectionId={ID} intensity={0.7} />
      <Drift from={card} to={405} amount={0.02}>
        <Lockup liftAt={card} />
      </Drift>

      <Headline
        top={600}
        text="Your phone's senses, for Hermes."
        start={o1.s + 30}
        stagger={2}
        size={64}
        exitAt={o2.s - 8}
      />
      <Headline
        top={590}
        text="It asks before it acts."
        start={o2.s}
        stagger={2}
        size={88}
        accent={["asks"]}
        exitAt={card - 10}
      />

      {/* end card: drifts until the final 1.5 s, then holds still */}
      <Drift from={card} to={405} amount={0.02}>
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: 440,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 14,
          }}
        >
          <Reveal at={card + 4} rise={20}>
            <div
              style={display(44, {
                fontWeight: 600,
                fontStretch: "110%",
                letterSpacing: "-0.015em",
                color: "rgba(241,241,238,.82)",
              })}
            >
              Your phone&apos;s senses, for Hermes.
            </div>
          </Reveal>
          <Reveal at={card + 8} rise={14}>
            <div
              style={{
                ...mono(17, { color: C.blueText }),
                marginTop: 12,
                marginBottom: 18,
              }}
            >
              Open source · Built for Hermes Agent
            </div>
          </Reveal>
          <Reveal at={card + 11} rise={20}>
            <Link>phone-senses.pages.dev</Link>
          </Reveal>
          <Reveal at={card + 14} rise={20}>
            <Link pulseAt={o4.s + 24}>github.com/LSUDOKO/Phone-Senses</Link>
          </Reveal>
          <Reveal at={card + 18} rise={14}>
            <div style={{ ...mono(18, { color: C.paper }), marginTop: 22 }}>
              Built by Arpit Singh · Hamirpur, HP
            </div>
          </Reveal>
        </div>
      </Drift>
      <div
        style={{ position: "absolute", left: 96, bottom: 56, maxWidth: 680 }}
      >
        <Reveal at={card + 24} rise={0}>
          <div style={mono(13, { letterSpacing: "0.06em" })}>
            Music: &ldquo;Space Voyage&rdquo; by Ekilorea Sound (CC0) · Sources:
            NPCI · McAfee · MHA / PIB · Gu et al. 2026
          </div>
        </Reveal>
      </div>
    </AbsoluteFill>
  );
};
