from enum import Enum, unique

import requests

import db
from .http import (
    COURTLISTENER_BASE_URL, OPINION_CLUSTER_FILTERS, OPINION_INSTANCE_FILTERS,
    filters_to_url_params, get_response_json
)
import regex
from .utils import warn


def _assert_unit_list(obj):
    if not isinstance(obj, list) or len(obj) != 1:
        raise ValueError  # TODO (custom unexpected value error?)


class _Insertable(object):
    def insert(self, db_connection):
        raise NotImplementedError


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
        db_connection.cursor().execute(sql, (
            # Sqlite3 requires unicode.
            self.shorthand.decode('utf-8'),
            self.short_name.decode('utf-8'),
            self.fullname.decode('utf-8')
        ))


class CaseFiling(_Insertable):
    def __init__(self, docket_entry, http_session=requests):
        self._docket_entry = docket_entry
        self._http_session = http_session
        self._opinion_cluster = None
        self._opinion = None

        self.fetch_opinion_cluster()
        self.fetch_opinion()

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

    def insert(self, db_connection):
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
        db_connection.cursor().execute(sql, (
            self.docket_number,
            self.url,
            self.plain_text,
            self.sha1,
            self.filed_on
        ))

    def __get(self, endpoint, filter_dict):
        filtered_endpoint = endpoint + filters_to_url_params(filter_dict)
        response = self._http_session.get(filtered_endpoint)
        return get_response_json(response)

    def fetch_opinion_cluster(self):
        clusters = self._docket_entry.get('clusters')
        _assert_unit_list(clusters)
        self._opinion_cluster = self.__get(clusters[0], OPINION_CLUSTER_FILTERS)

    def fetch_opinion(self):
        opinions = self._opinion_cluster.get('sub_opinions')
        _assert_unit_list(opinions)
        self._opinion = self.__get(opinions[0], OPINION_INSTANCE_FILTERS)

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

    def __str__(self):
        return self.name.lower().replace('_', ' ')

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
        self.concurring_justices = regex.split_justices(concurring_assocs)
        if concurring_chief:
            self.concurring_justices += [concurring_chief]
        # Get the OpinionType enum value
        if isinstance(type_, OpinionType):
            self.type = type_
        else:
            self.type = OpinionType.to_type(type_)
        # Set (and if necessary, prompt) the effective type
        self.effective_type = self.type
        if self.type == OpinionType.CONCURRING_AND_DISSENTING:
            self._prompt_effective_type()
        self.id = None

    @property
    def utf8_authoring_justice(self):
        return self.authoring_justice.encode('utf-8')

    @property
    def utf8_concurring_justices(self):
        return [justice.encode('utf-8')
                for justice in self.concurring_justices]

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
                self.effective_type.value,
                # The try block is for this line: get() may return None.
                Justice.get(self.authoring_justice).shorthand
            )
        except AttributeError:
            return None

    def insert(self, db_connection):
        sql = """
            INSERT INTO opinions (
                case_filing_docket_number,
                opinion_type_id,
                effective_op_type,
                authoring_justice
            )
            VALUES (?, ?, ?, ?);
        """
        if self._sql_tuple is None:
            msg = (
                "Encountered unknown authoring justice '{}' in {}".format(
                    self.authoring_justice.encode('utf-8'),
                    repr(self)
                )
            )
            warn(msg)
            return False
        db_connection.cursor().execute(sql, self._sql_tuple)
        # TODO: does this work since changes made by cursors on the same
        #  connection are visible to each other before commit? If so,
        #  alter get_id().
        self.get_id(db_connection)
        print(self.id)
        return True

    def get_id(self, db_connection=None):
        if self.id is not None:
            # The ID has already been cached so just return it.
            return self.id
        sql = """
            SELECT id FROM opinions
            WHERE case_filing_docket_number = ?
                AND opinion_type_id = ?
                AND effective_op_type = ?
                AND authoring_justice = ?;
        """
        try:
            cur = db_connection.cursor()
            cur.execute(sql, self._sql_tuple)
            # Cache the ID.
            (self.id,) = cur.fetchone()
            return self.id
        except AttributeError:
            db_connection = db.connect()
            try:
                return self.get_id(db_connection)
            finally:
                db_connection.close()

    def __str__(self):
        return '{} Opinion [{}] by {}'.format(
            str(self.type).upper(),
            self.case_filing.docket_number,
            self.utf8_authoring_justice
        )

    def __repr__(self):
        return '<{} Opinion [{}]: {} ({})>'.format(
            str(self.type).upper(),
            self.case_filing.docket_number,
            self.utf8_authoring_justice,
            ', '.join(self.utf8_concurring_justices)
        )

    def _prompt_effective_type(self):
        if self.type != OpinionType.CONCURRING_AND_DISSENTING:
            raise ValueError("Prompting effective type for non-Concurring and Dissenting opinion: " + repr(self))
        concur_inputs = ['concurring', 'c', '[c]oncurring']
        dissent_inputs = ['dissenting', 'd', '[d]issenting']
        valid_inputs_str = '[c]oncurring / [d]issenting'
        prompt = (
            "\n"
            "Case {} has a Concurring and Dissenting opinion that needs "
            "to be classified as either Concurring OR Dissenting for "
            "calculation. Please visit the URL below to review the opinion text:\n"
            "\n"
            "{}\n"
            "\n"
            "Effective Type of {}\n"
            "({}): "
        ).format(self.case_filing, self.case_filing.url, self, valid_inputs_str)
        while True:
            effective_type = raw_input(prompt).lower()
            if effective_type in concur_inputs:
                self.effective_type = OpinionType.CONCURRING
                break
            elif effective_type in dissent_inputs:
                self.effective_type = OpinionType.DISSENTING
                break
            prompt = (
                "Invalid input. Try one of the following: {}\n"
                "Effective Type of {} ({}): "
            ).format(
                ', '.join(concur_inputs + dissent_inputs),
                self,
                valid_inputs_str
            )


class MajorityOpinion(Opinion):
    def __init__(self, case_filing, authoring_justice, concurring_chief,
                 concurring_assocs):
        super(MajorityOpinion, self).__init__(case_filing, authoring_justice,
                                              OpinionType.MAJORITY,
                                              concurring_chief,
                                              concurring_assocs)
