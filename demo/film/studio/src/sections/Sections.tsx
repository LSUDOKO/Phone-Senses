import React from "react";
import { AbsoluteFill, Series, useVideoConfig } from "remotion";
import { C } from "../brand";
import { sectionFrames } from "../motion";
import vo from "../data/vo.json";
import { ColdOpen } from "./ColdOpen";
import { Title } from "./Title";
import { Problem } from "./Problem";
import { Turn } from "./Turn";
import { UnderTheHood } from "./UnderTheHood";
import { Impact } from "./Impact";
import { Outro } from "./Outro";

const PARTS: [string, React.FC][] = [
  ["cold", ColdOpen],
  ["title", Title],
  ["problem", Problem],
  ["turn", Turn],
  ["hood", UnderTheHood],
  ["impact", Impact],
  ["outro", Outro],
];

/** Film frames covered by these sections (walkthrough excluded). */
export const sectionsDuration = (fps: number) =>
  PARTS.reduce((a, [id]) => a + sectionFrames(id, fps), 0);
export const SECTION_IDS = vo.sections
  .map((s) => s.id)
  .filter((id) => PARTS.some(([p]) => p === id));

/** Preview: all motion-graphics sections back to back. */
export const Sections: React.FC = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: C.ink }}>
      <Series>
        {PARTS.map(([id, Comp]) => (
          <Series.Sequence
            key={id}
            name={id}
            durationInFrames={sectionFrames(id, fps)}
          >
            <Comp />
          </Series.Sequence>
        ))}
      </Series>
    </AbsoluteFill>
  );
};
