/** Every word of 《痛苦和坚持 · NO.02 预期》, and when it is said. Times are film seconds. */
export type TimedText = {
    readonly id: string;
    readonly text: string;
    readonly start: number;
    readonly end: number;
};
/** The choreography is written at this length; the SVML window can be shorter. */
export declare const AUTHORED_SECONDS = 97.5;
export declare const LINES: readonly TimedText[];
export declare const STATEMENTS: readonly TimedText[];
