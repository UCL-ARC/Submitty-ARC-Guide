from ..md2tex import mdcomment2tex

def tests_mdcomment2text_code_and_format():
    text_input = "Code in `laboratory.py`, implementing the `single` full experiment reaction as in: `+`: `'lower: [{}]'.format(','.join(lower))`"
    text_expected = "Code in \\texttt{laboratory.py}, implementing the \\texttt{single} full experiment reaction as in: \\texttt{+}: \\texttt{'lower: [{}]'.format(','.join(lower))}"
    assert text_expected == mdcomment2tex(text_input)

def tests_mdcomment2text_newlines():
    text_input = """Missing help for the arguments. How does a user knows what the `--reactions` flag for?\n `%s` is a very old way to print on strings. `.format` is preferred."""
    text_expected = """Missing help for the arguments. How does a user knows what the \\texttt{----reactions} flag for? \\newline  \\texttt{\\%s} is a very old way to print on strings. \\texttt{.format} is preferred."""
    assert text_expected == mdcomment2tex(text_input)

def tests_mdcomment2text_symbols():
    text_input = "Multiline strings can be concatenated by using `()` and without a need for a `\\` at the end of each line."
    text_expected = "Multiline strings can be concatenated by using \\texttt{()} and without a need for a \\texttt{\\textbackslash} at the end of each line."
    assert text_expected == mdcomment2tex(text_input)

def tests_mdcomment2text_multicode():
    text_input = "Not meaningful messages on many commits (E.g.: `commit all`, `i = 2`" # `update .. file`, etc)."
    text_expected = "Not meaningful messages on many commits (E.g.: \\texttt{commit all}, \\texttt{i = 2}" # \\texttt{update .. file}, etc)."
    assert text_expected == mdcomment2tex(text_input)


def tests_mdcomment2text_style_code():
    text_input = "Not **meaningful** messages on _many commits_ (E.g.: `commit all`, `i = 2`" # `update .. file`, etc)."
    text_expected = "Not \\textbf{meaningful} messages on \\emph{many commits} (E.g.: \\texttt{commit all}, \\texttt{i = 2}" # \\texttt{update .. file}, etc)."
    assert text_expected == mdcomment2tex(text_input)


def tests_mdcomment2text_code_hyphons():
    text_input = "Good binning `['0-9', '10-19', ...]` with `['0-19', ...]` test missing."
    text_expected = r"Good binning \texttt{['0--9', '10--19', ...]} with \texttt{['0--19', ...]} test missing."
    assert text_expected == mdcomment2tex(text_input)
