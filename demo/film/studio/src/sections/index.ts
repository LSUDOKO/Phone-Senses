import type React from "react";
import { ColdOpen } from "./ColdOpen";
import { Impact } from "./Impact";
import { Outro } from "./Outro";
import { Problem } from "./Problem";
import { Title } from "./Title";
import { Turn } from "./Turn";
import { UnderTheHood } from "./UnderTheHood";

/** Motion-graphics sections keyed by vo.json section id. Frame 0 = the section's start in vo.json. */
export const SECTIONS: Record<string, React.FC> = {
  cold: ColdOpen,
  title: Title,
  problem: Problem,
  turn: Turn,
  hood: UnderTheHood,
  impact: Impact,
  outro: Outro,
};

export { sectionFrames, sectionStartFrame } from "../motion";
