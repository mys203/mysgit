/** Everything the film says, and when it says it. Times are film seconds. */
/** The persistent bottom line. One of these is readable at any moment. */
export const LINES = [
    { id: "l01", text: "先看一眼：这 12 个点，你能记住几个？", start: 0.4, end: 5.8 },
    { id: "l02", text: "绝大多数人，停在 4 到 7 之间。", start: 5.8, end: 11.9 },
    { id: "l03", text: "1956 年，心理学家米勒给了这个数字一个名字：7±2。", start: 12.0, end: 18.9 },
    { id: "l04", text: "它不是智商，是你的工作记忆容量：同一时刻能抓住的东西数量。", start: 19.0, end: 29.7 },
    { id: "l05", text: "1946 年，荷兰棋手德赫罗特做了几乎一样的实验，只是把点换成了棋子。", start: 30.2, end: 38.6 },
    { id: "l06", text: "他给国际象棋大师和新手看真实棋局，五秒钟，然后让他们复原。", start: 38.6, end: 46.9 },
    { id: "l07", text: "大师几乎全能摆对，新手错得一塌糊涂。", start: 47.0, end: 52.2 },
    { id: "l08", text: "于是结论看上去很简单：大师记性更好。", start: 52.4, end: 58.4 },
    { id: "l09", text: "可研究者把棋子随机撒在棋盘上，又做了一遍。", start: 58.6, end: 64.2 },
    { id: "l10", text: "这一次，大师和新手几乎一样差。", start: 64.4, end: 70.0 },
    { id: "l11", text: "差距不在记得多，而在记得什么。", start: 70.2, end: 78.2 },
    { id: "l12", text: "大师看到的不是一个一个棋子，而是三五个一组的关系。", start: 78.4, end: 88.3 },
    { id: "l13", text: "12 个棋子，在他们眼里是 4 件事，不是 12 件。", start: 88.4, end: 97.2 },
    { id: "l14", text: "这就是组块。工作记忆装的是块，不是零件。", start: 97.3, end: 104.2 },
    { id: "l15", text: "所以学得慢，常常不是脑子的问题。", start: 104.6, end: 112.2 },
    { id: "l16", text: "是你还在一个一个字地看，别人已经一整块一整块地看。", start: 112.4, end: 121.4 },
    { id: "l17", text: "怎么练？别重复读，去反复提取。", start: 121.6, end: 128.3 },
    { id: "l18", text: "合上资料，把刚学的讲一遍。讲不出来的地方，就是还没长成块的地方。", start: 128.4, end: 134.6 },
    { id: "l19", text: "组块是练出来的，不是聪明出来的。", start: 134.8, end: 142.0 },
    { id: "l20", text: "参考：de Groot (1946) 国际象棋思维研究；Chase & Simon (1973) 组块理论", start: 142.2, end: 146.2 },
];
/** The hero statements in the stage band. */
export const STATEMENTS = [
    { id: "s01", text: "你能记住几个？", start: 0.8, end: 5.4 },
    { id: "s02", text: "7 ± 2", start: 12.4, end: 18.6 },
    { id: "s03", text: "1946 · 棋盘", start: 30.8, end: 37.4 },
    { id: "s04", text: "换成随机棋局", start: 58.8, end: 63.8 },
    { id: "s05", text: "优势消失", start: 64.6, end: 69.8 },
    { id: "s06", text: "12 → 4", start: 88.6, end: 96.8 },
    { id: "s07", text: "组块", start: 97.6, end: 103.8 },
    { id: "s08", text: "整块 还是 零件", start: 112.6, end: 120.8 },
    { id: "s09", text: "讲得出来，才算学会", start: 128.6, end: 134.4 },
    { id: "s10", text: "练出来的", start: 134.9, end: 141.8 },
];
/** The through-line: 12 pieces on a board, shown as twelve things then as four. */
export const PIECE_SQUARES = [
    [1, 0], [3, 0], [4, 0], [2, 1], [5, 1], [0, 2],
    [6, 3], [2, 4], [5, 5], [1, 6], [4, 6], [7, 7],
];
export const SCRAMBLED_SQUARES = [
    [6, 0], [0, 1], [7, 2], [3, 3], [1, 4], [6, 4],
    [0, 5], [4, 5], [2, 6], [7, 6], [3, 7], [5, 7],
];
export const CHUNK_GROUPS = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11],
];
//# sourceMappingURL=content.js.map