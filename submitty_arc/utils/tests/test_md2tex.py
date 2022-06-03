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

def tests_mdcomment2tex_something_fails():
    text_input = "Your computed value for the C02 emitted appears to be wrong. You calculate the slope values as `((self.elevation[i] / self.elevation[i-1]) - 1) * 100` where `self.elevations` is the list of elevation values for the track, but this should instead be something like `((self.elevation[i] - self.elevation[i-1]) / step_size) * 100` where `step_size` is the horizontal distance travelled in each step in the same units as elevation."
    text_expected = r"Your computed value for the C02 emitted appears to be wrong. You calculate the slope values as \texttt{((self.elevation[i] / self.elevation[i--1]) -- 1) * 100} where \texttt{self.elevations} is the list of elevation values for the track, but this should instead be something like \texttt{((self.elevation[i] -- self.elevation[i--1]) / step\_size) * 100} where \texttt{step\_size} is the horizontal distance travelled in each step in the same units as elevation."
    assert text_expected == mdcomment2tex(text_input)

def test_greaters():
    text_input = "Initialisation of vector does not need a for loop if all elements are the same. Can be done by specifying the size and value i.e for a `vector<vector<bool>> grid: grid(10, std::vector<bool>(10, false)`. Or if using arrays then `std::fill`."
    text_expected = r"Initialisation of vector does not need a for loop if all elements are the same. Can be done by specifying the size and value i.e for a \texttt{vector<vector<bool>> grid: grid(10, std::vector<bool>(10, false)}. Or if using arrays then \texttt{std::fill}."
    assert text_expected == mdcomment2tex(text_input)


def test_multiplecc():

    text_input = "Spacing could be improved, e.g. `if ((i!= row)||(j!=column))` or `for(int i=digit;i<argc;++i)`"
    text_expected = r"Spacing could be improved, e.g. \texttt{if ((i!= row)||(j!=column))} or \texttt{for(int i=digit;i<argc;++i)}"
    assert text_expected == mdcomment2tex(text_input)


def test_ampersands():

    text_input = "Inconsistent use of spacing, e.g. `if(row+1>=start && row+1<rows_ && col>=start && col<columns_ && vec2D_[row+1][col] == 'o')`"
    text_expected = r"Inconsistent use of spacing, e.g. \texttt{if(row+1>=start \&\& row+1<rows\_ \&\& col>=start \&\& col<columns\_ \&\& vec2D\_[row+1][col] == 'o')}"
    assert text_expected == mdcomment2tex(text_input)

def test_with_maths():
    text_input = "Should use for loops for tests instead of integrating timestep multiple times. $s = s0 + ut + 0.5 * a * t^2$ not correctly implemented in unit test 1b (const acceleration)."
    text_expected = "Should use for loops for tests instead of integrating timestep multiple times. \(s = s0 + ut + 0.5 * a * t^2\) not correctly implemented in unit test 1b (const acceleration)."
    assert text_expected == mdcomment2tex(text_input)
