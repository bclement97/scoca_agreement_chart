# encoding=utf8
from __future__ import print_function

import sqlite3
import string
import sys
from time import time
import warnings

# import click as cli

import agreement_chart
from .db import start_db
from .http import (
    DOCKET_LIST_ENDPOINT, DOCKET_LIST_FILTERS,
    filters_to_url_params, get_response_json, start_http_session
)
from .models import CaseFiling, Justice, MajorityOpinion, Opinion, OpinionType
import regex
from .utils import project_path, warn


def main():
    http_session = start_http_session()
    try:
        db_conn = start_db()
        try:
            flagged_case_filings = set()
            for case_filing in get_active_docket(http_session):
                # CaseFilings whose docket numbers end in a letter. Only 'A'
                # and 'M' are known to occur, but others should be flagged
                # regardless.
                if case_filing.docket_number[-1] in string.ascii_letters:
                    flagged_case_filings.add(case_filing)
                    # Ignore flagged case filings for now.
                    warn('Ignoring {}'.format(case_filing))
                    continue
                # TODO: save case filings
                for opinion in get_opinions(case_filing):
                    # Case Filing has no opinions.
                    if opinion is None:
                        flagged_case_filings.add(case_filing)
                        break
                    # TODO: save opinions
                # _, _, _ = save_opinions(db_conn, opinions)
            # _, _ = save_active_docket(db_conn, active_docket)
        finally:
            db_conn.close()
    finally:
        http_session.close()


def get_active_docket(http_session, filters=DOCKET_LIST_FILTERS):
    next_page = DOCKET_LIST_ENDPOINT + filters_to_url_params(filters)
    while True:
        response = get_response_json(http_session.get(next_page))
        for docket_entry in response['results']:
            yield CaseFiling(docket_entry, http_session)
        next_page = response.get('next')
        if not next_page:
            return


def save_active_docket(db_connection, active_docket):
    """Inserts CaseFilings from ACTIVE_DOCKET into DB_CONNECTION,
    ignoring ones that already exist in the table.

    :param db_connection: The database connection
    :param active_docket: An iterable of CaseFilings
    :return: First return value is a list of inserted CaseFilings.
    Second return value is a list of ignored CaseFilings.
    """

    sql = """
        INSERT INTO case_filings (
            docket_number,
            url,
            plain_text,
            sha1,
            filed_on
        )
        VALUES (?, ?, ?, ?, ?);
    """

    inserted, ignored = [], []
    for case_filing in active_docket:
        try:
            # Automatically commit on success.
            with db_connection:
                db_connection.execute(sql, (
                    case_filing.docket_number,
                    case_filing.url,
                    case_filing.plain_text,
                    case_filing.sha1,
                    case_filing.filed_on
                ))
        except sqlite3.IntegrityError:
            # Ignore case filings whose docket numbers already exist in
            # the table.
            ignored += [case_filing]
        else:
            inserted += [case_filing]

    return inserted, ignored


def get_opinions(case_filing):
    opinion_tuples = regex.findall_opinions(case_filing.plain_text)
    if not len(opinion_tuples):
        # Case Filing has no opinions.
        yield None
        return
    majority_tuple, secondary_tuples = opinion_tuples[0], opinion_tuples[1:]
    yield MajorityOpinion(case_filing, *majority_tuple[:3])
    for tup in secondary_tuples:
        yield Opinion(case_filing, *tup[3:])


def save_opinions(db_connection, opinions):
    insert_opinion_sql = """
        INSERT INTO opinions (
            case_filing_docket_number,
            opinion_type_id,
            effective_op_type,
            authoring_justice_id
        )
        VALUES (?, ?, ?, ?);
    """
    opinion_id_sql = """
        SELECT id FROM opinions
        WHERE case_filing_docket_number = ?
            AND opinion_type_id = ?
            AND effective_op_type = ?
            AND authoring_justice_id = ?;
    """
    concurrence_sql = """
        INSERT INTO concurrences (
            opinion_id,
            justice_id
        )
        VALUES (?, ?);
    """
    justices = Justice.get_all_by_short_name(db_connection)

    # FIXME: This logic looks digusting. Does it even work?

    inserted, ignored, partial = [], [], []
    for opinion in opinions:
        # Insert the opinion.
        authoring_justice = justices.get(opinion.authoring_justice)
        if authoring_justice is None:
            msg = (
                "Encountered unknown authoring justice '{}' in {}"
                .format(
                    opinion.authoring_justice.encode('utf-8'),
                    repr(opinion)
                )
            )
            warn(msg)
            continue
        opinion_sql_tuple = (
            opinion.case_filing.docket_number,
            opinion.type.value,
            opinion.effective_type.value,
            authoring_justice.id
        )
        try:
            with db_connection:
                db_connection.execute(insert_opinion_sql, opinion_sql_tuple)
        except sqlite3.IntegrityError:
            ignored += [opinion]
        else:
            inserted += [opinion]
        # Get the ID of the inserted opinion.
        cur = db_connection.execute(opinion_id_sql, opinion_sql_tuple)
        (opinion_id,) = cur.fetchone()
        # Insert a concurrence row for each concurring justice.
        for concurring_justice_name in opinion.concurring_justices:
            concurring_justice = justices.get(concurring_justice_name)
            if concurring_justice is None:
                # See if we missed justices due to bad formatting
                # E.g., a missing comma between names
                justice_names, unknown_name = regex.findall_and_reduce(
                    justices.keys(),
                    concurring_justice_name
                )
                if justice_names:
                    # Add the newly discovered concurring justices to
                    # the opinion so that this loop will come back to them.
                    opinion.concurring_justices.extend(justice_names)
                if unknown_name:
                    # Part or all of the unknown name remains
                    msg = (
                        "Encountered unknown concurring justice '{}' in {}"
                        .format(
                            concurring_justice_name.encode('utf-8'),
                            repr(opinion)
                        )
                    )
                    warn(msg)
                continue
            try:
                with db_connection:
                    db_connection.execute(concurrence_sql, (
                        opinion_id,
                        concurring_justice.id
                    ))
            except sqlite3.IntegrityError:
                partial += [opinion]

    return inserted, ignored, partial


def build():
    def create_chart(justices):
        """Creates an chart between 7 justices.

        The keys are frozensets of justice ID pairs so that the ID order
        doesn't matter. Each pair is set to a default value of a list of two
        sets, where the first value in the total number of agreements and
        the second value is the total number of agreements and disagreements."""
        chart = {}
        for i, j1 in enumerate(justices):
            for j2 in justices[i+1:]:
                key = frozenset([j1.id, j2.id])
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

    def print_chart(chart, justices):
        for i, j1 in enumerate(justices):
            for j2 in justices[i+1:]:
                key = frozenset([j1.id, j2.id])
                print('({}, {}): {}'.format(j1.id, j2.id, chart[key]))

    def create_concurrence_dict(justices):
        return {j.id: [set(), set()] for j in justices}

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
            authoring_justice_id author_id,
            c.justice_id
        FROM opinions o
            JOIN opinion_types ot ON effective_op_type = ot.id
            LEFT JOIN concurrences c ON o.id = c.opinion_id
        ORDER BY docket_num, ot.id, author_id;
    """

    db_conn = start_db()
    try:
        db_conn.row_factory = sqlite3.Row

        justices = Justice.get_all(db_conn)
        count_chart = create_chart(justices)
        concurrence = create_concurrence_dict(justices)
        parent_op = None

        for op in db_conn.execute(opinion_sql):
            (docket_num, op_id, type_id, type_str, author_id, justice_id) = op
            # When we encounter a new docket number, ensure that it's a
            # majority opinion (by nature of the SQL ordering).-=
            if parent_op is None or parent_op['docket_num'] != docket_num:
                assert type_id == OpinionType.MAJORITY.value
                if parent_op is not None:
                    # Encountered a new, non-first case filing.
                    update_chart(count_chart, concurrence)
                    concurrence = create_concurrence_dict(justices)
                parent_op = op

            if type_id == OpinionType.MAJORITY.value:
                if justice_id:
                    concurrence_add_concur(author_id, justice_id)
            elif type_id == OpinionType.CONCURRING.value:
                concurrence_add_concur(parent_op['author_id'], author_id)
                if justice_id:
                    concurrence_add_concur(parent_op['author_id'], justice_id)
                    concurrence_add_concur(author_id, justice_id)
            elif type_id == OpinionType.DISSENTING.value:
                concurrence_add_dissent(parent_op['author_id'], author_id)
                if justice_id:
                    concurrence_add_dissent(parent_op['author_id'], justice_id)
                    concurrence_add_concur(author_id, justice_id)
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
        f.write(agreement_chart.generate(rate_chart, justices))
        print('Exported "{}"'.format(filepath))


if __name__ == '__main__':
    # Hack for dealing with unicode strings
    # https://markhneedham.com/blog/2015/05/21/python-unicodeencodeerror-ascii-codec-cant-encode-character-uxfc-in-position-11-ordinal-not-in-range128/
    reload(sys)
    sys.setdefaultencoding('utf8')

    main()
    build()
