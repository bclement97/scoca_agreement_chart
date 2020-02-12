from enum import Enum, unique
import string

import apsw
import requests

from .http import (
    COURTLISTENER_BASE_URL, OPINION_CLUSTER_FILTERS, OPINION_INSTANCE_FILTERS,
    filters_to_url_params, get_response_json
)
import regex
import utils


def _assert_unit_list(obj):
    if not isinstance(obj, list) or len(obj) != 1:
        raise ValueError  # TODO (custom unexpected value error?)


class _Insertable(object):
    def insert(self, db_connection):
        raise NotImplementedError

    def _insert(self, db_connection, sql, bindings):
        utils.log('Inserting {}', self)
        cur = db_connection.cursor()
        try:
            cur.execute(sql, bindings)
        except apsw.ConstraintError as e:
            # Usually, this means it already exists in the database, so
            # just raise a warning just in case.
            utils.warn(str(e))
        return cur


class Justice(_Insertable):
    _all = []
    _all_by_shorthand = dict()
    _all_by_short_name = dict()

    def __init__(self, shorthand, short_name, fullname):
        self.shorthand = shorthand
        self.short_name = short_name
        self.fullname = fullname
        # Cache the justice by shorthand and short name for lookup.
        Justice._all.append(self)
        Justice._all_by_shorthand[shorthand] = self
        Justice._all_by_short_name[short_name] = self

    @staticmethod
    def get(justice):
        if justice in Justice._all_by_shorthand:
            return Justice._all_by_shorthand.get(justice)
        elif justice in Justice._all_by_short_name:
            return Justice._all_by_short_name.get(justice)
        else:
            return None

    @staticmethod
    def all():
        return Justice._all

    @staticmethod
    def all_short_names():
        return Justice._all_by_short_name.keys()

    def insert(self, db_connection):
        sql = """
            INSERT INTO justices (
                shorthand,
                short_name,
                fullname
            )
            VALUES (?, ?, ?); 
        """
        self._insert(db_connection, sql, (
            self.shorthand,
            self.short_name,
            self.fullname
        ))

    def __str__(self):
        return '{} ({})'.format(self.fullname, self.shorthand)


class CaseFiling(_Insertable):
    def __init__(self, docket_entry, http_session=requests):
        self.opinions = []

        self._docket_entry = docket_entry
        self._http_session = http_session
        self._opinion_cluster = None
        self._opinion = None

        self._fetch_opinion_cluster()
        self._fetch_opinion()
        self._parse_opinions()

    @property
    def docket_number(self):
        return self._docket_entry.get('docket_number')

    @property
    def url(self):
        abs_url = self._opinion_cluster.get('absolute_url')
        return COURTLISTENER_BASE_URL + abs_url if abs_url else None

    @property
    def plain_text(self):
        return self._opinion.get('plain_text')

    @property
    def sha1(self):
        return self._opinion.get('sha1')

    @property
    def filed_on(self):
        return self._opinion_cluster.get('date_filed')

    @property
    def ends_in_letter(self):
        return self.docket_number[-1] in string.ascii_letters

    @property
    def has_no_opinions(self):
        return not len(self.opinions)

    def insert(self, db_connection):
        sql = """
            INSERT INTO case_filings (
                docket_number,
                url,
                plain_text,
                sha1,
                filed_on,
                ends_in_letter_flag,
                no_opinions_flag
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        self._insert(db_connection, sql, (
            self.docket_number,
            self.url,
            self.plain_text,
            self.sha1,
            self.filed_on,
            self.ends_in_letter,
            self.has_no_opinions
        ))

    def __get(self, endpoint, filter_dict):
        filtered_endpoint = endpoint + filters_to_url_params(filter_dict)
        response = self._http_session.get(filtered_endpoint)
        return get_response_json(response)

    def _fetch_opinion_cluster(self):
        clusters = self._docket_entry.get('clusters')
        _assert_unit_list(clusters)
        self._opinion_cluster = self.__get(clusters[0], OPINION_CLUSTER_FILTERS)

    def _fetch_opinion(self):
        opinions = self._opinion_cluster.get('sub_opinions')
        _assert_unit_list(opinions)
        self._opinion = self.__get(opinions[0], OPINION_INSTANCE_FILTERS)

    def _parse_opinions(self):
        opinion_tuples = regex.findall_opinions(self.plain_text)
        if len(opinion_tuples):
            majority_tuple, secondary_tuples = opinion_tuples[0], opinion_tuples[1:]
            self.opinions.append(MajorityOpinion(self, *majority_tuple[:3]))
            for tup in secondary_tuples:
                self.opinions.append(Opinion(self, *tup[3:]))

    def __str__(self):
        return self.docket_number

    def __repr__(self):
        return '<CaseFiling: {}>'.format(self.docket_number)


@unique
class OpinionType(Enum):
    MAJORITY = 1
    CONCURRING = 2
    DISSENTING = 3
    CONCURRING_AND_DISSENTING = 4

    def __eq__(self, other):
        if type(other) is int:
            return self.value == other
        elif self.__class__ is other.__class__:
            return self.value == other.value
        return NotImplemented

    def __str__(self):
        return self.name.lower().replace('_', ' ')

    # TODO: rename/split
    @staticmethod
    def to_type(val):
        if isinstance(val, (str, unicode)):
            return OpinionType[val.upper().replace(' ', '_')]
        elif isinstance(val, int):
            return OpinionType[val]
        raise NotImplementedError


class Opinion(_Insertable):
    def __init__(self, case_filing, authoring_justice, type_, concurring_chief,
                 concurring_assocs):
        self.case_filing = case_filing
        self.authoring_justice = authoring_justice
        # Put concurring justices (chief and assoc.) into a list
        # TODO: convert these to Justice objects
        self.concurring_justices = regex.split_justices(concurring_assocs)
        if concurring_chief:
            self.concurring_justices += [concurring_chief]
        # Get the OpinionType enum value
        if isinstance(type_, OpinionType):
            self.type = type_
        else:
            self.type = OpinionType.to_type(type_)
        self.effective_type = None
        self.id = None

    @property
    def _sql_tuple(self):
        """Returns a tuple uniquely identifying this opinion to use in
         sql queries.

        Returns None if the authoring justice is not recognized (is not
        in the Justices table.
        """
        try:
            return (
                self.case_filing.docket_number,
                self.type.value,
                # The try block is for this line: get() may return None.
                Justice.get(self.authoring_justice).shorthand
            )
        except AttributeError:
            return None

    def insert(self, db_connection):
        sql = """
            INSERT INTO opinions (
                docket_number,
                type_id,
                authoring_justice
            )
            VALUES (?, ?, ?);
        """
        if self._sql_tuple is None:
            msg = "Encountered unknown authoring justice '{}' in {}"
            utils.warn(msg, self.authoring_justice, repr(self))
            return False
        cur = self._insert(db_connection, sql, self._sql_tuple)
        self._fetch_id(cur)
        return True

    def _fetch_id(self, cursor):
        sql = """
            SELECT id FROM opinions
            WHERE docket_number = ?
                AND type_id = ?
                AND authoring_justice = ?;
        """
        cursor.execute(sql, self._sql_tuple)
        # Cache the ID.
        (self.id,) = cursor.fetchone()
        return self.id

    def __str__(self):
        return '{} Opinion [{}] by {}'.format(
            str(self.type).upper(),
            self.case_filing.docket_number,
            self.authoring_justice
        )

    def __repr__(self):
        return '<{} Opinion [{}]: {} ({})>'.format(
            str(self.type).upper(),
            self.case_filing.docket_number,
            self.authoring_justice,
            ', '.join(self.concurring_justices)
        )

    # def _prompt_effective_type(self):
    #     if self.type != OpinionType.CONCURRING_AND_DISSENTING:
    #         raise ValueError("Prompting effective type for non-Concurring and Dissenting opinion: " + repr(self))
    #     concur_inputs = ['concurring', 'c', '[c]oncurring']
    #     dissent_inputs = ['dissenting', 'd', '[d]issenting']
    #     valid_inputs_str = '[c]oncurring / [d]issenting'
    #     prompt = (
    #         "\n"
    #         "Case {} has a Concurring and Dissenting opinion that needs "
    #         "to be classified as either Concurring OR Dissenting for "
    #         "calculation. Please visit the URL below to review the opinion text:\n"
    #         "\n"
    #         "{}\n"
    #         "\n"
    #         "Effective Type of {}\n"
    #         "({}): "
    #     ).format(self.case_filing, self.case_filing.url, self, valid_inputs_str)
    #     while True:
    #         effective_type = raw_input(prompt).lower()
    #         if effective_type in concur_inputs:
    #             self.effective_type = OpinionType.CONCURRING
    #             break
    #         elif effective_type in dissent_inputs:
    #             self.effective_type = OpinionType.DISSENTING
    #             break
    #         prompt = (
    #             "Invalid input. Try one of the following: {}\n"
    #             "Effective Type of {} ({}): "
    #         ).format(
    #             ', '.join(concur_inputs + dissent_inputs),
    #             self,
    #             valid_inputs_str
    #         )


class MajorityOpinion(Opinion):
    def __init__(self, case_filing, authoring_justice, concurring_chief,
                 concurring_assocs):
        super(MajorityOpinion, self).__init__(case_filing, authoring_justice,
                                              OpinionType.MAJORITY,
                                              concurring_chief,
                                              concurring_assocs)
