import type { FontStackRef } from "@hypit/media";
import type { Timeline } from "@hypit/timeline";
import type { SpatialFrame } from "@hypit/spatial";
import type { TemporalWindow } from "@hypit/temporal";
export type SceneOptions = {
    readonly id: string;
    readonly title: string;
    readonly tag: string;
};
/** A one-off scene for 《痛苦和坚持》: every frame is computed from the requested frame alone. */
export declare function renderScene(timeline: Timeline, within: SpatialFrame, window: TemporalWindow, font: FontStackRef, options: SceneOptions): import("@hypit/composition").VisualTrack;
