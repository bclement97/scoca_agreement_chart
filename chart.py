import sqlite3
from time import time
import yattag

import db
from .models import Justice, OpinionType
from .utils import project_path


_CSS_PATH = project_path('chart.css')


def build():
    def create_chart(justices):
        """Creates a chart between 7 justices.

        The keys are frozensets of justice ID pairs so that the ID order
        doesn't matter. Each pair is set to a default value of a list of two
        sets, where the first value in the total number of agreements and
        the second value is the total number of agreements and disagreements."""
        chart = {}
        for i, j1 in enumerate(justices):
            for j2 in justices[i+1:]:
                key = frozenset([j1.shorthand, j2.shorthand])
                chart[key] = [0, 0]
        return chart

    def update_chart(chart, concurrence_dict):
        for id1 in concurrence_dict:
            concur_ids, dissent_ids = concurrence[id1]
            for id2 in concur_ids:
                # Justices can't concur with themselves.
                if id1 != id2:
                    key = frozenset([id1, id2])
                    chart[key][0] += 1
                    chart[key][1] += 1
            for id2 in dissent_ids:
                # Justices can't dissent with themselves.
                if id1 != id2:
                    key = frozenset([id1, id2])
                    chart[key][1] += 1

    def create_concurrence_dict(justices):
        return {j.shorthand: [set(), set()] for j in justices}

    def concurrence_add_concur(author_id, justice_id):
        # Justices can't concur with themselves.
        if author_id != justice_id:
            concurrence[author_id][0].add(justice_id)

    def concurrence_add_dissent(author_id, justice_id):
        # Justices can't dissent with themselves.
        if author_id != justice_id:
            concurrence[author_id][1].add(justice_id)

    opinion_sql = """
        SELECT
            case_filing_docket_number docket_num,
            o.id opinion_id,
            effective_op_type type_id,
            type type_str, -- used for displaying
            authoring_justice author,
            c.justice
        FROM opinions o
            JOIN opinion_types ot ON effective_op_type = ot.id
            LEFT JOIN concurrences c ON o.id = c.opinion_id
        ORDER BY docket_num, ot.id, author;
    """

    db_conn = db.connect()
    try:
        db_conn.row_factory = sqlite3.Row

        justices = Justice.all()
        count_chart = create_chart(justices)
        concurrence = create_concurrence_dict(justices)
        parent_op = None

        for op in db_conn.execute(opinion_sql):
            (docket_num, op_id, type_id, type_str, author, justice) = op
            # When we encounter a new docket number, ensure that it's a
            # majority opinion (by nature of the SQL ordering).
            if parent_op is None or parent_op['docket_num'] != docket_num:
                assert type_id == OpinionType.MAJORITY.value
                if parent_op is not None:
                    # Encountered a new, non-first case filing.
                    update_chart(count_chart, concurrence)
                    concurrence = create_concurrence_dict(justices)
                parent_op = op

            if type_id == OpinionType.MAJORITY.value:
                if justice:
                    concurrence_add_concur(author, justice)
            elif type_id == OpinionType.CONCURRING.value:
                concurrence_add_concur(parent_op['author'], author)
                if justice:
                    concurrence_add_concur(parent_op['author'], justice)
                    concurrence_add_concur(author, justice)
            elif type_id == OpinionType.DISSENTING.value:
                concurrence_add_dissent(parent_op['author'], author)
                if justice:
                    concurrence_add_dissent(parent_op['author'], justice)
                    concurrence_add_concur(author, justice)
            else:
                assert type_id == OpinionType.CONCURRING_AND_DISSENTING.value
                assert False, (
                    "Effective type for Opinion ID#{} incorrectly set " +
                    "to 'Concurring and Dissenting'"
                ).format(op_id)
    finally:
        db_conn.close()

    update_chart(count_chart, concurrence)
    rate_chart = create_chart(justices)
    for k, counts in count_chart.iteritems():
        rate_chart[k] = round(counts[0] * 100.0 / counts[1], 2)

    filepath = project_path('out', 'agreement_chart_{}.html'.format(int(time())))
    with open(filepath, 'w+') as f:
        f.write(generate(rate_chart, justices))
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
                line('td', j.fullname.encode('utf-8'))

    return doc.getvalue() if not indent else yattag.indent(doc.getvalue(),
                                                           indentation='  ',
                                                           newline='\n')


def print_chart(chart, justices):
    for i, j1 in enumerate(justices):
        for j2 in justices[i+1:]:
            key = frozenset([j1.shorthand, j2.shorthand])
            print('({}, {}): {}'.format(j1.shorthand, j2.shorthand, chart[key]))