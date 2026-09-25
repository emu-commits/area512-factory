#!/usr/bin/env python3
"""Verify every claim in prompts/rules.md against a512sim (AREA512's interpreter
config). Each snippet runs alone. Exit 1 if any expectation is wrong."""
import pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
OK = [
    'print("{}".format(3), "{:>5}".format(3), "{:.1f}".format(2.25), "{:^10}".format("a"))',
    'print(2**40, 7 // 2, divmod(7, 2), round(2.567, 1), abs(-2))',
    'l = [3, 1, 2]; l.sort(); l.reverse(); l.insert(0, 9); l.remove(9); print(l.copy(), l.count(1), l.index(2))',
    'l = [1, 2, 3]; del l[0]; print(l.pop(0), l)',
    'd = {"a": 1}; d.setdefault("b", 2); d.update({"c": 3}); print(d.pop("a"), sorted(d.keys()), list(d.values()), d.get("z", 0))',
    's = " Ab1 "; print(s.strip().lower(), s.lstrip(), s.rstrip(), "ab".upper(), "12".isdigit(), "ab".isalpha(), " ".isspace())',
    'print("a,b".split(","), "abc".find("b"), "abc".index("c"), "abc".replace("b", "x"), "-".join(["a", "b"]), "ab".startswith("a"), "ab".endswith("b"))',
    'print(sorted([3, 1], reverse=True), sorted(["bb", "a"], key=len), sum([1, 2]), any([0, 1]), all([1]))',
    'print(list(zip([1], [2])), list(map(str, [1])), [i * i for i in range(3)], {k: 1 for k in "ab"})',
    'def g():\n    yield 1\n    yield 2\nprint(list(g()))',
    'def mk(n):\n    def f(x):\n        return x + n\n    return f\nprint(mk(2)(3))',
    'def f(*a, **k):\n    return len(a) + len(k)\nprint(f(1, 2, b=3))',
    'try:\n    1 / 0\nexcept ZeroDivisionError:\n    print("ok")\nfinally:\n    pass',
    'print(chr(65), ord("A"), hex(255), repr("a"), isinstance(1.0, float), int("42"), float("1.5"), str(3), bool(0), tuple([1]))',
    'class A:\n    def __init__(self):\n        self.x = 1\nclass B(A):\n    pass\nprint(B().x)',
    'print("abc"[0], "abc"[-1], [1, 2][1])',
    'print(RNG.random_int() % 6 >= 0, sleep_ms(1))',
    'SD.write("/home/ai/t.txt", "hi"); print(SD.read("/home/ai/t.txt"), File.exist("/home/ai/t.txt"))',
]
FAIL = [
    'import math', 'import time', 'import random', 'import json',
    'print("hello"[1:3])', 'print([1, 2, 3][:2])', 'print("abc"[::-1])',
    'x = 5\nprint(f"{x}")', 'print("%d" % 3)',
    'print(min(1, 2))', 'print(max([1, 2]))', 'print(list(enumerate([1])))',
    'print(list(reversed([1, 2])))', 'print(list(filter(None, [0, 1])))',
    'print({1, 2})', 'print(set())', 'print(frozenset())',
    'print(a := 3)', 'async def f():\n    pass',
    'class A:\n    @property\n    def x(self):\n        return 1\nprint(A().x)',
    'print("ab".center(6))', 'print("a=b".partition("="))', 'print("a\\nb".splitlines())',
    'print("aab".count("a"))', 'print("ab".title())', 'print("1".zfill(3))',
    'print("a".ljust(3))', 'print("a".rjust(3))', 'print(bytearray(2))',
    'Sprite(10, 10).rect(1.5, 0, 2, 2, 0)', 'Sprite(10, 10).text(x=0, y=0, string="a", color=0)',
    'File("/a").write("x")',
]


def run(src):
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "t.py"
        p.write_text(src + "\n")
        k = pathlib.Path(d) / "k"
        k.write_text("")
        r = subprocess.run([str(HERE / "a512sim"), str(HERE / "prelude.py"), str(k), "64", str(p)],
                           capture_output=True, text=True, timeout=10)
        return "@@EXIT ok" in r.stdout, r.stdout


def main():
    wrong = 0
    for expect, cases in ((True, OK), (False, FAIL)):
        for src in cases:
            ok, out = run(src)
            if ok != expect:
                wrong += 1
                print("WRONG (expected {}): {!r}\n{}".format("ok" if expect else "fail", src, out))
    print("{} checks, {} wrong".format(len(OK) + len(FAIL), wrong))
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
