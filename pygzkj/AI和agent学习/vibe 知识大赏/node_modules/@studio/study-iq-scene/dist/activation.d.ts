import type { ModuleManifest } from "@hypit/hypit/protocol";
import type { StructuredSurfaceHandler } from "@hypit/hypit/markup";
export declare const manifest: ModuleManifest;
export declare const decodeSurface: StructuredSurfaceHandler;
export declare const hypitPackage: {
    format: "hypit.package@1";
    modules: {
        manifest: ModuleManifest;
    }[];
    facets: {
        readonly abi: string;
        readonly offers?: readonly string[];
        readonly implementation: unknown;
    }[];
};
export default hypitPackage;
