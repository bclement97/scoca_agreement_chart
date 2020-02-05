from time import time
import yattag

import db
from .models import Justice, OpinionType
import utils


_CSS_PATH = utils.project_path('chart.css')


def build():
    def concurring_justices(opinion_id):
        """Returns a set of concurring justice IDs for the given OPINION_ID."""
        sql = 'SELECT justice FROM concurrences WHERE opinion_id = ?'
        cur = db_connection.cursor()
        cur.execute(sql, (opinion_id,))
        return {row[0] for row in cur}

    majority_opinions_sql = """
        SELECT
            docket_number,
            id,
            authoring_justice
        FROM majority_opinions;
    """
    secondary_opinions_sql = """
        SELECT
            id,
            type_id,
            effective_type_id,
            authoring_justice
        FROM secondary_opinions
        WHERE docket_number = ?
        ORDER BY type_id, effective_type_id, authoring_justice;
    """

    all_justices = Justice.all()
    # We keep a list of two ints for each pair of justices representing,
    # respectively, the number of times they concur and the total number
    # of times they concur or dissent.
    count_chart = {}
    for i, j1 in enumerate(all_justices):
        for j2 in all_justices[i+1:]:
            key = frozenset([j1.shorthand, j2.shorthand])
            count_chart[key] = [0, 0]

    db_connection = db.connect()
    try:
        majority_cur = db_connection.cursor()
        majority_cur.execute(majority_opinions_sql)
        for docket_num, majority_id, majority_author in majority_cur:
            concurs = {j.shorthand: set() for j in all_justices}
            dissents = {j.shorthand: set() for j in all_justices}

            concurs[majority_author] |= concurring_justices(majority_id)

            secondary_cur = db_connection.cursor()
            secondary_cur.execute(secondary_opinions_sql, (docket_num,))
            for secondary_id, type_id, effective_type_id, secondary_author in secondary_cur:
                if type_id == OpinionType.CONCURRING_AND_DISSENTING:
                    if effective_type_id is None:
                        msg = "Effective type for CONCURRING AND DISSENTING Opinion" \
                              " ID#{} is not set".format(secondary_id)
                        utils.warn(msg)
                        continue
                else:
                    effective_type_id = type_id

                justices = concurring_justices(secondary_id)
                concurs[secondary_author] |= justices
                if effective_type_id == OpinionType.CONCURRING:
                    concurs[majority_author] |= justices | {secondary_author}
                elif effective_type_id == OpinionType.DISSENTING:
                    dissents[majority_author] |= justices | {secondary_author}
                else:
                    assert False

            for j1 in [j.shorthand for j in all_justices]:
                # Justices can't concur with/dissent from themselves,
                # so we don't include them if they're in the sets.
                for j2 in concurs[j1] - {j1}:
                    key = frozenset([j1, j2])
                    count_chart[key][0] += 1
                    count_chart[key][1] += 1
                for j2 in dissents[j1] - {j1}:
                    key = frozenset([j1, j2])
                    count_chart[key][1] += 1
    finally:
        db_connection.close()

    rate_chart = {}
    for key, counts in count_chart.iteritems():
        try:
            rate_chart[key] = counts[0] * 100.0 / counts[1]
        except ZeroDivisionError:
            rate_chart[key] = -1

    filepath = utils.project_path('out', 'agreement_chart_{}.html'.format(int(time())))
    with open(filepath, 'w+') as f:
        f.write(generate(rate_chart, all_justices))
        print('Exported "{}"'.format(filepath))


def generate(chart, justices, indent=False):
    doc, tag, text, line = yattag.Doc().ttl()

    with tag('style'), open(_CSS_PATH) as css:
        doc.asis(css.read())

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
                    key = frozenset([j_left.shorthand, j_top.shorthand])
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
                line('td', j.fullname)

    return doc.getvalue() if not indent else yattag.indent(doc.getvalue(),
                                                           indentation='  ',
                                                           newline='\n')


def print_chart(chart, justices):
    for i, j1 in enumerate(justices):
        for j2 in justices[i+1:]:
            key = frozenset([j1.shorthand, j2.shorthand])
            print('({}, {}): {}'.format(j1.shorthand, j2.shorthand, chart[key]))