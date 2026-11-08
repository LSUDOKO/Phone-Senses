import React from "react";
import { Composition, delayRender, continueRender } from "remotion";
import { fontsReady } from "./brand";
import { StyleFrames } from "./StyleFrames";
import { Sections, sectionsDuration } from "./sections/Sections";
import { Walkthrough } from "./sections/Walkthrough";
import { Film, filmDuration } from "./Film";
import { Cut, CUT_SECONDS } from "./Cut";
import { sectionFrames } from "./motion";

const fontHandle = delayRender("brand fonts");
fontsReady.then(() => continueRender(fontHandle));

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="StyleFrames" component={StyleFrames} durationInFrames={420} fps={30} width={1920} height={1080} />
      <Composition id="Sections" component={Sections} durationInFrames={sectionsDuration(30)} fps={30} width={1920} height={1080} />
      <Composition id="Walkthrough" component={Walkthrough} durationInFrames={sectionFrames("walk", 30)} fps={30} width={1920} height={1080} />
      <Composition id="Film" component={Film} durationInFrames={filmDuration(30)} fps={30} width={1920} height={1080} />
      <Composition id="Cut" component={Cut} durationInFrames={Math.round(CUT_SECONDS * 30)} fps={30} width={1920} height={1080} />
    </>
  );
};
