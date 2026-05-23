#!/usr/bin/env python3
"""
Author: R K K Jinendra

Description:
    This will counts the words in a LaTeX document while ignoring
    comments, math, tables, figures, citations, and bibliography content.
"""

import re
import sys
from pathlib import Path

EXCLUDED_ENVS = [
    "abstract",
    "acknowledgement",
    "acknowledgements",
    "acknowledgment",
    "acknowledgments",
    "table",
    "table*",
    "tabular",
    "tabular*",
    "longtable",
    "sidewaystable",
    "figure",
    "figure*",
    "acronym",
    "acronyms",
    "thebibliography",
]

EXCLUDED_CMDS = [
    "caption",
    "captionof",
    "footnote",
    "footnotetext",
    "thanks",
    "tableofcontents",
    "listoffigures",
    "listoftables",
    "bibliography",
    "printbibliography",
    "label",
    "ref",
    "eqref",
    "pageref",
    "cite",
    "citet",
    "citep",
    "citealt",
    "citealp",
    "nocite",
    "autoref",
    "url",
]

# Commands whose argument text should be kept
KEEP_TEXT_COMMANDS = [
    "textbf", "textit", "emph", "underline", "texttt", "textrm",
    "textsc", "textsl", "textnormal", "href"
]

def strip_comments(tex: str) -> str:
    # Remove LaTeX comments, but keep escaped \%
    return re.sub(r"(?<!\\)%.*", "", tex)

def remove_math(tex: str) -> str:
    # Remove common math regions so symbols don't count as words
    patterns = [
        r"\$\$.*?\$\$",
        r"\$.*?\$",
        r"\\\[.*?\\\]",
        r"\\\(.*?\\\)",
        r"\\begin\{equation\*?\}.*?\\end\{equation\*?\}",
        r"\\begin\{align\*?\}.*?\\end\{align\*?\}",
        r"\\begin\{multline\*?\}.*?\\end\{multline\*?\}",
        r"\\begin\{gather\*?\}.*?\\end\{gather\*?\}",
    ]
    for pat in patterns:
        tex = re.sub(pat, " ", tex, flags=re.DOTALL)
    return tex

def remove_excluded_envs(tex: str) -> str:
    for env in EXCLUDED_ENVS:
        pat = rf"\\begin\{{{re.escape(env)}\}}.*?\\end\{{{re.escape(env)}\}}"
        while True:
            new_tex = re.sub(pat, " ", tex, flags=re.DOTALL)
            if new_tex == tex:
                break
            tex = new_tex
    return tex

def keep_second_arg_of_href(tex: str) -> str:
    # \href{url}{visible text} -> visible text
    return re.sub(r"\\href\s*\{[^{}]*\}\s*\{([^{}]*)\}", r"\1", tex)

def unwrap_formatting_commands(tex: str) -> str:
    # Convert \textbf{hello} -> hello
    # Repeatedly apply because there may be nested commands
    changed = True
    while changed:
        changed = False
        new_tex = re.sub(
            r"\\(?:"
            + "|".join(map(re.escape, KEEP_TEXT_COMMANDS[:-1]))
            + r")\*?(?:\[[^\]]*\])?\{([^{}]*)\}",
            r"\1",
            tex,
        )
        # Special handling for \href already converted above, so no need here.
        if new_tex != tex:
            changed = True
            tex = new_tex
    return tex

def remove_excluded_commands(tex: str) -> str:
    # Remove commands that should not contribute any text
    # This removes the command and any immediate braced groups after it.
    for cmd in EXCLUDED_CMDS:
        # Matches \cmd, optionally with [..], and any number of simple {...} groups after it
        pat = rf"\\{re.escape(cmd)}\*?(?:\s*\[[^\]]*\])*(?:\s*\{{[^{{}}]*\}})*"
        tex = re.sub(pat, " ", tex)
    return tex

def remove_remaining_commands(tex: str) -> str:
    # Remove any leftover LaTeX commands, but keep their braced content later if already unwrapped
    tex = re.sub(r"\\[a-zA-Z@]+(?:\*?)", " ", tex)
    return tex

def remove_braces_and_specials(tex: str) -> str:
    # Clean residual braces and TeX punctuation
    tex = tex.replace("{", " ").replace("}", " ")
    tex = tex.replace("~", " ")
    tex = tex.replace("^", " ")
    tex = tex.replace("_", " ")
    tex = re.sub(r"[|`´]+", " ", tex)
    return tex

def normalize(tex: str) -> str:
    tex = re.sub(r"\s+", " ", tex)
    return tex.strip()

def count_words(tex: str) -> int:
    # Unicode-friendly word matcher; excludes numbers-only tokens
    words = re.findall(r"[^\W\d_]+(?:[-'][^\W\d_]+)*", tex, flags=re.UNICODE)
    return len(words)

def latex_word_count(tex: str) -> tuple[int, str]:
    tex = strip_comments(tex)
    tex = remove_math(tex)
    tex = remove_excluded_envs(tex)
    tex = re.sub(r"\\tableofcontents\b|\\listoffigures\b|\\listoftables\b", " ", tex)
    tex = keep_second_arg_of_href(tex)
    tex = unwrap_formatting_commands(tex)
    tex = remove_excluded_commands(tex)
    tex = remove_remaining_commands(tex)
    tex = remove_braces_and_specials(tex)
    tex = normalize(tex)
    return count_words(tex), tex

def main():
    if len(sys.argv) != 2:
        print("Usage: python count_latex_words.py yourfile.tex")
        sys.exit(1)

    path = Path(sys.argv[1])
    tex = path.read_text(encoding="utf-8", errors="ignore")
    count, cleaned = latex_word_count(tex)

    print(f"Word count: {count}")

if __name__ == "__main__":
    main()
