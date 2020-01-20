# encoding=utf8
from __future__ import print_function

import apsw
import unicodecsv as csv  # This helps fix unicode issues.
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
from .models import CaseFiling, Justice, OpinionType
import regex
import utils


def init():
    db_connection = db.connect()
    try:
        # Load justices from CSV config file and populate the justice table.
        justices_path = utils.project_path('config', 'justices.csv')
        try:
            with db_connection, open(justices_path, 'rb') as justices_csv:
                justices_reader = csv.DictReader(justices_csv)
                # TODO: change?
                for row in justices_reader:
                    justice = Justice(row['shorthand'], row['short_name'],
                                      row['fullname'])
                    justice.insert(db_connection)
        except Exception:
            utils.print_err('Could not populate table `justices`')
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
            utils.print_err('Could not populate table `opinion_types`')
            raise
    finally:
        db_connection.close()


def main():
    # TODO: for future use
    flagged_cases = set()

    def flag(case_filing, msg):
        flagged_cases.add(case_filing)
        utils.warn(msg.format(case_filing), stacklevel=2)

    http_session = start_http_session()
    try:
        db_connection = db.connect()
        try:
            for case_filing in get_active_docket(http_session):
                # CaseFilings whose docket numbers end in a letter. Only 'A'
                # and 'M' are known to occur, but others should be flagged
                # regardless.
                if case_filing.docket_number[-1] in string.ascii_letters:
                    # TODO: Ignore flagged case filings for now.
                    flag(case_filing, 'Ignoring {}')
                    continue

                inserted_opinions = insert_case(db_connection, case_filing)
                if inserted_opinions is None:
                    # Case filing was not inserted.
                    continue

                if not len(inserted_opinions):
                    flag(case_filing, '{} has no opinions')
                else:
                    insert_concurrences(db_connection, inserted_opinions)
        finally:
            db_connection.close()
    finally:
        http_session.close()


def get_active_docket(http_session, filters=DOCKET_LIST_FILTERS):
    next_page = DOCKET_LIST_ENDPOINT + filters_to_url_params(filters)
    while next_page:
        response = get_response_json(http_session.get(next_page))
        for docket_entry in response['results']:
            yield CaseFiling(docket_entry, http_session)
        next_page = response.get('next')


def insert_case(db_connection, case_filing):
    # Begin and commit transaction for inserting the case
    # filing and its opinions.
    inserted_opinions = []
    try:
        with db_connection:
            case_filing.insert(db_connection)
            for opinion in case_filing.opinions:
                # Case Filing has no opinions.
                if opinion is None:
                    break
                if opinion.insert(db_connection):
                    inserted_opinions.append(opinion)
    except (apsw.Error, sqlite3.Error) as e:
        utils.print_err('Could not insert {} - {}'.format(
            case_filing.docket_number,
            e
        ))
        # Case filing and opinions not inserted, so no
        # concurrences to insert.
        return None
    return inserted_opinions


def insert_concurrences(db_connection, opinions):
    assert len(opinions), 'There should always be at least one opinion (majority).'
    # Insert concurrences.
    sql = """
        INSERT INTO concurrences (
            opinion_id,
            justice
        )
        VALUES (?, ?);
    """
    concurrences = []
    for op in opinions:
        # Insert a concurrence row for each concurring justice.
        for concurring_justice_name in op.concurring_justices:
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
                    op.concurring_justices.extend(justice_names)
                if unknown_name:
                    # Part or all of the unknown name remains
                    msg = (
                        "Encountered unknown concurring justice '{}' in {}".format(
                            concurring_justice_name,
                            repr(op)
                        )
                    )
                    utils.warn(msg)
                continue
            concurrences.append((op.id, concurring_justice.shorthand))
    assert len(concurrences), 'There are no concurrences; the majority opinion always has some.'
    try:
        with db_connection:
            db_connection.cursor().executemany(sql, concurrences)
    except (apsw.Error, sqlite3.Error) as e:
        docket_number = opinions[0].case_filing.docket_number
        utils.print_err('Could not insert concurrences for {} - {}'.format(
            docket_number,
            e
        ))


if __name__ == '__main__':
    # Hack for dealing with unicode strings
    # https://markhneedham.com/blog/2015/05/21/python-unicodeencodeerror-ascii-codec-cant-encode-character-uxfc-in-position-11-ordinal-not-in-range128/
    reload(sys)
    sys.setdefaultencoding('utf8')

    init()
    main()
    chart.build()
