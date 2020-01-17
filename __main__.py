# encoding=utf8
from __future__ import print_function

import apsw
import unicodecsv as csv  # This fixes many Unicode issues.
import sqlite3
import string
import sys

# import click as cli

import chart
import db
from .http import (
    DOCKET_LIST_ENDPOINT, DOCKET_LIST_FILTERS,
    filters_to_url_params, get_response_json, start_http_session
)
from .models import CaseFiling, Justice, MajorityOpinion, Opinion, OpinionType
import regex
from .utils import print_err, project_path, warn


def init():
    db_connection = db.connect()
    # Load justices from CSV config file and populate the justice table.
    justices_path = project_path('config', 'justices.csv')
    try:
        with db_connection, open(justices_path, 'rb') as justices_csv:
            justices_reader = csv.DictReader(justices_csv)
            # TODO: change?
            for row in justices_reader:
                justice = Justice(row['shorthand'], row['short_name'],
                                  row['fullname'])
                justice.insert(db_connection)
    except Exception:
        print_err('Could not populate table `justices`')
        raise
    # Populate the opinion type table.
    opinion_types_sql = 'INSERT INTO opinion_types (type) VALUES (?);'
    try:
        with db_connection:
            db_connection.cursor().executemany(
                opinion_types_sql,
                [(str(op_type),) for op_type in list(OpinionType)]
            )
    except Exception:
        print_err('Could not populate table `opinion_types`')
        raise


def main():
    http_session = start_http_session()
    try:
        db_connection = db.connect()
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
            # Begin and commit transaction for inserting the case
            # filing and its opinions.
            try:
                with db_connection:
                    case_filing.insert(db_connection)
                    inserted_opinions = []
                    for opinion in parse_opinions(case_filing):
                        # Case Filing has no opinions.
                        if opinion is None:
                            flagged_case_filings.add(case_filing)
                            break
                        if opinion.insert(db_connection):
                            inserted_opinions.append(opinion)
            except (apsw.Error, sqlite3.Error) as e:
                print_err('Could not insert {} - {}'.format(
                    case_filing.docket_number,
                    e
                ))
                # Case filing and opinions not inserted, so no
                # concurrences to insert.
                continue
            # Insert concurrences.
            concurrence_sql = """
                INSERT INTO concurrences (
                    opinion_id,
                    justice
                )
                VALUES (?, ?);
            """
            concurrences = []
            for opinion in inserted_opinions:
                opinion_id = opinion.get_id()
                # Insert a concurrence row for each concurring justice.
                for concurring_justice_name in opinion.concurring_justices:
                    concurring_justice = Justice.get(concurring_justice_name)
                    # TODO: move this to Opinion constructor?
                    if concurring_justice is None:
                        # See if we missed justices due to bad formatting
                        # E.g., a missing comma between names
                        justice_names, unknown_name = regex.findall_and_reduce(
                            Justice.all_short_names(),
                            concurring_justice_name
                        )
                        if justice_names:
                            # Add the newly discovered concurring justices to
                            # the opinion so that this loop will come back to them.
                            opinion.concurring_justices.extend(justice_names)
                        if unknown_name:
                            # Part or all of the unknown name remains
                            msg = (
                                "Encountered unknown concurring justice '{}' in {}".format(
                                    concurring_justice_name.encode('utf-8'),
                                    repr(opinion)
                                )
                            )
                            warn(msg)
                        continue
                    concurrences.append((opinion_id, concurring_justice.shorthand))
            try:
                with db_connection:
                    db_connection.cursor().executemany(concurrence_sql, concurrences)
            except (apsw.Error, sqlite3.Error) as e:
                print_err('Could not insert concurrences for {} - {}'.format(
                    case_filing.docket_number,
                    e
                ))
    finally:
        http_session.close()


def get_active_docket(http_session, filters=DOCKET_LIST_FILTERS):
    next_page = DOCKET_LIST_ENDPOINT + filters_to_url_params(filters)
    while next_page:
        response = get_response_json(http_session.get(next_page))
        for docket_entry in response['results']:
            yield CaseFiling(docket_entry, http_session)
        next_page = response.get('next')


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


def parse_opinions(case_filing):
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
            authoring_justice
        )
        VALUES (?, ?, ?, ?);
    """
    opinion_id_sql = """
        SELECT id FROM opinions
        WHERE case_filing_docket_number = ?
            AND opinion_type_id = ?
            AND effective_op_type = ?
            AND authoring_justice = ?;
    """
    concurrence_sql = """
        INSERT INTO concurrences (
            opinion_id,
            justice
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


if __name__ == '__main__':
    # Hack for dealing with unicode strings
    # https://markhneedham.com/blog/2015/05/21/python-unicodeencodeerror-ascii-codec-cant-encode-character-uxfc-in-position-11-ordinal-not-in-range128/
    reload(sys)
    sys.setdefaultencoding('utf8')

    init()
    main()
    chart.build()
