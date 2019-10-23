import yattag

from .models import Justice


def generate(chart, justices):
    doc, tag, text, line = yattag.Doc().ttl()

    css = """
#agreeTable {
  border: none;
  border-collapse: collapse;
}

#agreeTable th, #agreeTable td {
  width: 6em;
  height: 3em;
  text-align: center;
  vertical-align: middle;
}

#agreeTable th {
  border: none;
  color: #222;
}

#agreeTable td {
  border: solid 2px black;
  padding: 0;
}

.low, .red {
  background-color: #ff9d9d;
}

.high, .green {
  background-color: #b1efb1;
}

#legendTable {
  border: none;
  border-collapse: collapse;
}

#legendTable td {
  border: solid 1px #000;
  padding: 0.25em 0.5em;
}
"""
    with tag('style'):
        doc.asis(css)

    with tag('table', id='agreeTable'):
        # Top labels
        with tag('tr'):
            line('th', '')
            for j in justices[1:]:
                line('th', j.shorthand)
        # Left labels and chart body
        for col, j_left in enumerate(justices):
            with tag('tr'):
                # Left space
                if col > 0:
                    line('th', '', colspan=col)
                # Left label
                line('th', j_left.shorthand)
                # Chart body
                for j_top in justices[col+1:]:
                    key = frozenset([j_left.id, j_top.id])
                    rate = int(round(chart[key]))
                    with tag('td'):
                        if rate > 90:
                            doc.attr(klass='high')
                        elif rate < 10:
                            doc.attr(klass='low')
                        text('{}%'.format(rate))

    with tag('table', id='legendTable'):
        for j in justices:
            with tag('tr'):
                line('td', j.shorthand)
                line('td', j.fullname.encode('utf-8'))

    return yattag.indent(
        doc.getvalue(),
        indentation='  ',
        newline='\n'
    )
