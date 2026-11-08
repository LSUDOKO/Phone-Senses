import { Video } from "@remotion/media";
import React from "react";
import { AbsoluteFill, Sequence, staticFile, useVideoConfig } from "remotion";
import { C, Callout, Field, GlassWindow, Kinetic, Label, Mark, MONO, PhoneFrame, SectionTag, Wordmark } from "./brand";

const ColdOpen: React.FC = () => (
  <AbsoluteFill>
    <Field intensity={0.7} />
    <Label style={{ left: 96, top: 72 }}>Hamirpur · exam week · 07:42</Label>
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <Kinetic text="214 notifications before breakfast." accent={["214"]} size={120} />
    </AbsoluteFill>
  </AbsoluteFill>
);

const TitleReveal: React.FC = () => (
  <AbsoluteFill>
    <Field tone="paper" />
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "row", gap: 40 }}>
      <Mark size={190} start={0} />
      <Wordmark size={176} start={14} />
    </AbsoluteFill>
    <Label style={{ left: 96, bottom: 72, top: "auto" }} delay={30}>Give Hermes your phone's senses</Label>
  </AbsoluteFill>
);

const Walkthrough: React.FC = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill>
      <Field intensity={0.55} />
      <SectionTag index="05" title="Morning brief" />
      <div style={{ position: "absolute", left: 96, top: 150 }}>
        <GlassWindow title="hermes chat · phone-senses" width={1180} height={800}>
          <Video src={staticFile("footage/test-battery/term.mp4")} trimBefore={10 * fps} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top left" }} muted />
        </GlassWindow>
      </div>
      <PhoneFrame height={800} style={{ position: "absolute", right: 150, top: 120 }} label="Real phone · moto g34">
        <Video src={staticFile("footage/test-battery/phone.mp4")} style={{ width: "100%", height: "100%", objectFit: "cover" }} muted />
      </PhoneFrame>
      <Callout text="Real Android data" x={1450} y={540} start={10} side="left" />
    </AbsoluteFill>
  );
};

const UnderTheHood: React.FC = () => (
  <AbsoluteFill>
    <Field intensity={0.9} />
    <SectionTag index="06" title="Under the hood" />
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 48 }}>
      <Kinetic text="One signed request." size={104} chrome />
      <div style={{ fontFamily: MONO, fontSize: 30, color: C.paper, background: "rgba(255,255,255,.04)", border: "1px dashed rgba(255,255,255,.2)", borderRadius: 18, padding: "28px 40px", lineHeight: 1.6 }}>
        <span style={{ color: C.blueText }}>GET</span>\n/v1/status\n1762594205\n9f2c…e1\n<span style={{ color: C.mist }}>sha256(body)</span>
      </div>
    </AbsoluteFill>
  </AbsoluteFill>
);

export const StyleFrames: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: C.ink }}>
    <Sequence durationInFrames={90} name="Cold open"><ColdOpen /></Sequence>
    <Sequence from={90} durationInFrames={90} name="Title"><TitleReveal /></Sequence>
    <Sequence from={180} durationInFrames={150} name="Walkthrough"><Walkthrough /></Sequence>
    <Sequence from={330} durationInFrames={90} name="Under the hood"><UnderTheHood /></Sequence>
  </AbsoluteFill>
);
