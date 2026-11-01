import { assertAttributes, assertEmptyElement, createMarkupSurfaceFacet, textAttribute } from "@hypit/hypit/markup";
import { canonicalize, sameType } from "@hypit/hypit/protocol";
import { sealGraphFragment } from "@hypit/hypit/author";
import { createProducerPackageFacet } from "@hypit/hypit/producer";
import { createAdmissionPackageFacet } from "@hypit/hypit/admission";
import { compositionTypes } from "@hypit/composition";
import { mediaTypes } from "@hypit/media";
import { timelineTypes } from "@hypit/timeline";
import { spatialTypes } from "@hypit/spatial";
import { temporalTypes } from "@hypit/temporal";
import { resolveTemporalContext, resolveTemporalWindowReference, temporalContextAttributeVocabulary, temporalWindowAttributeNames, temporalWindowAttributeVocabulary } from "@hypit/temporal/markup";
import { renderScene } from "./render.js";
const module = { name: "@studio/study-iq-scene", version: "1" };
const types = Object.fromEntries(["Options"].map((name) => [name, { module, name }]));
const producers = Object.fromEntries(["render"].map((name) => [name, { module, name }]));
export const manifest = {
    format: "hypit.module@1",
    ...module,
    dependencies: [
        compositionTypes.visualTrack, mediaTypes.fontStack, timelineTypes.timeline,
        spatialTypes.frame, temporalTypes.window,
    ].map((type) => ({ module: type.module })),
    types: [{ name: types.Options.name }],
    capabilities: [],
    producers: [{
            name: producers.render.name,
            inputs: [
                { name: "options", type: types.Options },
                { name: "timeline", type: timelineTypes.timeline },
                { name: "within", type: spatialTypes.frame },
                { name: "window", type: temporalTypes.window },
                { name: "font", type: mediaTypes.fontStack },
            ],
            outputs: [{ name: "visual", type: compositionTypes.visualTrack }],
            needs: [],
        }],
};
const inline = (record) => {
    if (record?.value.kind !== "inline")
        throw new Error("Study and IQ scene inputs must be inline values.");
    return record.value.value;
};
const value = (data) => ({ kind: "inline", value: canonicalize(data) });
const component = {
    producers: [{
            producer: producers.render,
            handler: ({ inputs }) => ({
                outputs: {
                    visual: value(renderScene(inline(inputs.timeline), inline(inputs.within), inline(inputs.window), inline(inputs.font), inline(inputs.options))),
                },
                needs: {},
            }),
        }],
};
export const decodeSurface = ({ element, resolveReference }) => {
    assertAttributes(element, ["id", "title", "tag", "timeline", "within", "font",
        ...temporalWindowAttributeNames]);
    assertEmptyElement(element);
    const id = textAttribute(element, "id");
    const context = resolveTemporalContext({ element, resolveReference });
    const window = resolveTemporalWindowReference({ element, resolveReference });
    const reference = (name, type) => {
        const raw = element.attributes[name];
        if (typeof raw !== "object" || raw.kind !== "reference")
            throw new Error(name + " must be a reference.");
        const found = resolveReference(raw.path);
        if (found === undefined || !sameType(found.type, type))
            throw new Error(name + " has the wrong Type.");
        return found;
    };
    const options = {
        id: id,
        title: textAttribute(element, "title"),
        tag: textAttribute(element, "tag"),
    };
    const records = [{ id: id + ".options", type: types.Options, value: value(options), range: element.range }];
    const inputs = [
        { name: "timeline", type: timelineTypes.timeline },
        { name: "within", type: spatialTypes.frame },
        { name: "font", type: mediaTypes.fontStack },
        { name: "window", type: temporalTypes.window },
        { name: "options", type: types.Options },
    ];
    const bindings = {
        timeline: context.timeline.ref,
        within: reference("within", spatialTypes.frame).ref,
        font: reference("font", mediaTypes.fontStack).ref,
        window: window.ref,
        options: { kind: "record", id: id + ".options" },
    };
    const input = (name) => ({ kind: "fragment-input", name });
    const operations = [{
            id: "render",
            producer: producers.render,
            inputs: {
                options: input("options"), timeline: input("timeline"), within: input("within"),
                window: input("window"), font: input("font"),
            },
            result: { kind: "output", name: "visual" },
        }];
    const fragment = sealGraphFragment({
        inputs,
        operations,
        exports: [{ name: "visual", type: compositionTypes.visualTrack, root: { kind: "fragment-operation", operation: "render" } }],
    });
    return {
        records,
        fragments: [fragment],
        components: [{
                id, fragment: fragment.id, inputs: bindings,
                outputs: { visual: id + ".visual" }, range: element.range,
            }],
        exports: [id + ".visual"],
    };
};
const declaration = {
    name: "scene",
    tag: "Scene",
    mode: "structured",
    outputs: [compositionTypes.visualTrack, ...Object.values(types)],
    vocabulary: {
        summary: "The 《学习与智商》 graphic scene: twelve marks, a board of pieces, and two ways to study, drawn from the requested frame.",
        attributes: [
            ...temporalContextAttributeVocabulary,
            ...temporalWindowAttributeVocabulary,
            ...["id", "title", "tag", "within", "font"].map((name) => ({
                name, kind: "expression", required: true, summary: name,
            })),
        ],
        children: [],
        ports: [{ name: "visual", type: compositionTypes.visualTrack, summary: "The complete graphic scene." }],
        example: '<study:Scene id="film" timeline={program.timeline} within={canvas.bounds} font={font} during={program.window} title="学习与智商" tag="NO.01 · 组块"/>',
    },
};
export const hypitPackage = {
    format: "hypit.package@1",
    modules: [{ manifest }],
    facets: [
        createProducerPackageFacet(component),
        createAdmissionPackageFacet(component),
        createMarkupSurfaceFacet({ module, declaration, handler: decodeSurface }),
    ],
};
export default hypitPackage;
//# sourceMappingURL=activation.js.map