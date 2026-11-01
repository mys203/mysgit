/** Everything the film says, and when it says it. Times are film seconds. */
export type TimedText = {
    readonly id: string;
    readonly text: string;
    readonly start: number;
    readonly end: number;
};
/** The persistent bottom line. One of these is readable at any moment. */
export declare const LINES: readonly TimedText[];
/** The hero statements in the stage band. */
export declare const STATEMENTS: readonly TimedText[];
/** The through-line: 12 pieces on a board, shown as twelve things then as four. */
export declare const PIECE_SQUARES: readonly (readonly [number, number])[];
export declare const SCRAMBLED_SQUARES: readonly (readonly [number, number])[];
export declare const CHUNK_GROUPS: readonly (readonly number[])[];
