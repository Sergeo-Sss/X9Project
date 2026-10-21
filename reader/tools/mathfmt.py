"""Turn slash fractions in an HTML fragment into stacked CSS fractions.

Conservative and tag-aware: only converts A/B when BOTH sides are a clean unit — a
number, a variable (with its <sub>/<sup>), a parenthesised group, or a function call /
root applied to one. Anything ambiguous is left as a slash. It never looks inside a
<sub>/<sup> (so a slash already in an exponent stays a slash), never treats the '/' of
a closing tag as a fraction, and protects decimal separators (0,3 / 2).
"""
import re

_TOKEN_RE = re.compile(r"<sub>.*?</sub>|<sup>.*?</sup>|<[^>]+>|.", re.S)
_DEC1 = ""  # placeholder for a decimal comma
_DEC2 = ""  # placeholder for a decimal dot


def _tokenize(frag):
    return _TOKEN_RE.findall(frag)


def _is_atomfrag(t):
    return t.startswith("<sub>") or t.startswith("<sup>")


def _is_atom(tokens, idx):
    t = tokens[idx]
    if _is_atomfrag(t):
        return True
    if len(t) != 1:        # any other tag
        return False
    return t.isalnum() or t in ("√", _DEC1, _DEC2)


def _is_alpha_prefix(t):
    return len(t) == 1 and (t.isalpha() or t == "√")


def _grab_left(tokens, i):
    """Return (start, end) token slice of the numerator ending just before '/'."""
    j = i - 1
    while j >= 0 and tokens[j] == " ":
        j -= 1
    end = i
    while j >= 0 and _is_atom(tokens, j):
        j -= 1
    word_start = j + 1
    if j >= 0 and tokens[j] == ")":
        depth, k = 0, j
        while k >= 0:
            if tokens[k] == ")":
                depth += 1
            elif tokens[k] == "(":
                depth -= 1
                if depth == 0:
                    break
            k -= 1
        if k < 0:
            return None
        p = k - 1
        while p >= 0 and _is_alpha_prefix(tokens[p]):
            p -= 1
        return p + 1, end
    if word_start < end:
        return word_start, end
    return None


def _grab_right(tokens, i):
    """Return (start, end) token slice of the denominator starting just after '/'."""
    n = len(tokens)
    j = i + 1
    while j < n and tokens[j] == " ":
        j += 1
    start = j
    p = j
    while p < n and _is_alpha_prefix(tokens[p]):
        p += 1
    if p < n and tokens[p] == "(":
        depth, k = 0, p
        while k < n:
            if tokens[k] == "(":
                depth += 1
            elif tokens[k] == ")":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        if k >= n:
            return None
        end = k + 1
        while end < n and _is_atom(tokens, end):
            end += 1
        return start, end
    end = j
    while end < n and _is_atom(tokens, end):
        end += 1
    if end > start:
        return start, end
    return None


def _strip_parens(h):
    """Drop one outer pair of parens if the whole unit is a single balanced group."""
    if not (h.startswith("(") and h.endswith(")")):
        return h
    depth, i, n = 0, 0, len(h)
    while i < n:
        c = h[i]
        if c == "<":
            gt = h.find(">", i)
            i = gt + 1 if gt >= 0 else n
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return h[1:-1] if i == n - 1 else h
        i += 1
    return h


def _merge_fmt(frag):
    """Collapse per-run `</strong><strong>` (and em) so a bold span is contiguous and
    a fraction captured inside it contains no stray formatting tags."""
    prev = None
    while prev != frag:
        prev = frag
        frag = re.sub(r"</(strong|em)>(\s*)<\1>", r"\2", frag)
    return frag


def fractionize_html(frag):
    frag = _merge_fmt(frag)
    frag = re.sub(r"(?<=\d),(?=\d)", _DEC1, frag)
    frag = re.sub(r"(?<=\d)\.(?=\d)", _DEC2, frag)
    tokens = _tokenize(frag)
    i = 0
    while i < len(tokens):
        if tokens[i] == "/":
            left = _grab_left(tokens, i)
            right = _grab_right(tokens, i)
            if left and right:
                ls, le = left
                rs, re_ = right
                num = _strip_parens("".join(tokens[ls:le]).strip())
                den = _strip_parens("".join(tokens[rs:re_]).strip())
                # Drop stray bold/italic tags so the stacked span stays balanced.
                num = re.sub(r"</?(strong|em)>", "", num)
                den = re.sub(r"</?(strong|em)>", "", den)
                num_plain = re.sub("<[^>]+>", "", num)
                den_plain = re.sub("<[^>]+>", "", den)
                # A unit with a Cyrillic letter is a word (и/или), not a variable.
                cyr = re.search(r"[А-Яа-яЁё]", num_plain + den_plain)
                # Only stack SIMPLE fractions. Leave big operators, nested fractions
                # and over-long parts as a slash — stacking them looks broken on the
                # tiny screen.
                big = re.search(r"[∑∫∏∮]", num_plain + den_plain)
                nested = 'class="frac"' in num or 'class="frac"' in den
                too_long = len(num_plain) > 16 or len(den_plain) > 16
                if num and den and not (cyr or big or nested or too_long):
                    frac = ('<span class="frac"><span class="fn">' + num
                            + '</span><span class="fd">' + den + "</span></span>")
                    tokens[ls:re_] = [frac]
                    i = ls + 1
                    continue
        i += 1
    out = "".join(tokens)
    return out.replace(_DEC1, ",").replace(_DEC2, ".")


if __name__ == "__main__":
    tests = [
        "M = ∫01 4x4 dx = 4/5",
        "(4/5)<sup>2</sup> = 2/3 − 16/25",
        "f(x) = 1/(b − a) при x",
        "M(X) = (b2 − a2) / (2(b − a)) = (a + b)/2",
        "σ = (b − a)/(2√3)",
        "1/(σ√(2π))",
        "x = −ln 0,3 / 2 ≈ 1,204 / 2",
        "r<sup>1/4</sup>",                     # slash inside exponent: must stay
        "χ²набл = ∑ (ni − Npi)<sup>2</sup> / (Npi)",
        "x = a + (b − a)·r и/или прочее",      # 'и/или' must NOT become a fraction
        "высоты равны ni/h или wi/h = ni/(Nh)",
    ]
    for t in tests:
        print(t, "\n  ->", fractionize_html(t), "\n")
