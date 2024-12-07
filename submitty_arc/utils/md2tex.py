import re

import markdown
import mdx_latex

def extra_latex(text):

    latex_mdx = mdx_latex.makeExtension()
    md = markdown.Markdown()
    latex_mdx.extendMarkdown(md)
    return md.convert(text)

def mdcomment2tex(text):
    pattern_doubleslash = re.compile(r'(?<!\$)\\')
    text = pattern_doubleslash.sub("\\textbackslash", text)
    #text = re.sub(r'\`(?P<code>\W?\w*\W*?)\`', r'\\texttt{\g<code>}',  text) # single words
    text = re.sub(r'`(?P<code>((\w*([^\w`]*)?)*))`', r'\\texttt{\g<code>}', text) # longer descriptions
    #text = re.sub(r"(`)(.+?)\1(`)", r"\\texttt{\1}", text)
    text = extra_latex(text)
    text = text.replace(r"REMOVEME", '')
    text = text.replace('_', '\\_')
    text = text.replace('-', '--')
    text = text.replace('\cdot', '*')
    text = text.replace('\<', '<')
    text = text.replace('&&', '\&\&')
    text = text.replace("<root>","").replace("</root>","").replace("\n","")
    return text
