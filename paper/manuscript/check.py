"""Hard checks on manuscript.md: length by section, sentence statistics, banned forms."""
import re, sys
from pathlib import Path
s = (Path(__file__).resolve().parent / "manuscript.md").read_text()
main = s[:s.index("## Declarations")]
ab = main[main.index("## Abstract"):main.index("## Introduction")]
main = main[main.index("## Introduction"):]
def prose(t):
    out = []
    code = False
    for line in t.split("\n"):
        if line.startswith("```"): code = not code; continue
        if code or line.startswith("|") or line.startswith("#") or line.startswith("![]") or line.startswith("**Table") or line.startswith("**Figure") or line.startswith("*Note.*") or line.startswith("**Box"):
            continue
        out.append(line)
    return "\n".join(out)
secs = re.split(r"\n## ", main)
tot = 0
for sec in secs:
    name = sec.split("\n")[0].replace("## ", "")
    n = len(prose(sec).split()); tot += n
    print(f"{n:6d}  {name}")
print(f"{tot:6d}  main text (prose only); with tables and captions {len(main.split())}")
p = prose(main)
p = re.sub(r"\b(e\.g|i\.e|et al|vs|cf)\.", r"\1", p)
sent = [x for x in re.split(r"(?<=[.?!])\s+", p) if len(x.split()) > 2]
L = [len(x.split()) for x in sent]
print("sentences", len(L), "mean", round(sum(L) / len(L), 1), "share >35 words", round(sum(l > 35 for l in L) / len(L), 3), "max", max(L))
for x in sent:
    if len(x.split()) > 38: print("LONG:", x[:160])
print("em dashes:", s.count("—"), "| ' we ':", len(re.findall(r"\b[Ww]e\b|\b[Oo]ur\b", s)), "| ' I ':", len(re.findall(r"\bI\b", main)))
codes = re.findall(r"\b(K[0-9]|F[123]|Q[0-9]|E[0-9]{1,2}|ELP|BLP|DLP|OLD20|IC|TCC)\b", s)
print("codes:", sorted(set(codes)))
us = re.findall(r"\b\w*(?:ization|izing|ized|ize|yze|yzed|avior|color|modeling|center)\w*\b", main)
print("US spellings:", sorted(set(us)))
print("genuinely/honestly etc:", re.findall(r"\b(genuinely|honestly|straightforward|crucially|importantly|notably|delve)\b", s))
ab_t = ab.split("\n\n")[1]
print("abstract words", len(ab_t.split()), "numerals", re.findall(r"\d[\d.,]*", ab_t))
