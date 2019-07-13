"""REGEX MODULE

It is recommended to always use OPINION_REGEX with re.findall() or re.finditer() since it will always match
OPINION_REGEX_MAJORITY before matching OPINION_REGEX_SECONDARY. If not, matches of OPINION_REGEX_MAJORITY must be
removed from the search string before attempting to match OPINION_REGEX_SECONDARY which can wrongly include what should
be matched by OPINION_REGEX_MAJORITY.

The unicode and case-insensitive flag should be set in most cases. This is because this regex may not always match due
to typos, or minor differences in punctuation between published opinions and may need to be
updated accordingly and/or handled manually.

Capturing Groups (by index, (*) denotes present but may be empty):
- OPINION_MAJORITY:
    0. Authoring Justice
    1. Concurring Chief Justice (*)
    2. Concurring assoc. Justices
- OPINION_SECONDARY:
    0. Authoring Justice
    1. Opinion type
    2. Concurring Chief Justice (*)
    3. Concurring assoc. Justices (*)
- OPINION: groups of OPINION_MAJORITY followed by groups of OPINION_SECONDARY
"""

import re

# Matches and returns the name of a Justice
_JUSTICE = r'Justice ([^.,]+?)'
# Matches and returns the name of the authoring Justice of the opinion.
_OPINION_AUTHOR = r'(?:Chief )?' + _JUSTICE + ' (?:authored|filed) '
# Matches and returns the name(s) of the Justice(s) who concur(s) with an opinion.
# A match with multiple Justices should be in the form of 'X and Y' or 'X, Y, [...] and Z'.
_OPINION_CONCURRING = r',? in which (?:Chief ' + _JUSTICE + ' and )?Justices? ([^.]+?) concurred'

# Matches and returns the names of the authoring Justice of the majority opinion and those who concur with it.
OPINION_MAJORITY = _OPINION_AUTHOR + 'the opinion of the court' + _OPINION_CONCURRING
# Like OPINION_REGEX_MAJORITY, except for all other opinions.
OPINION_SECONDARY = _OPINION_AUTHOR + 'a (concurring|dissenting|concurring and dissenting) opinion' \
                    '(?:' + _OPINION_CONCURRING + ')?'
# Matches OPINION_REGEX_MAJORITY first and then OPINION_REGEX_SECONDARY.
OPINION = r'(?:' + OPINION_MAJORITY + ')|(?:' + OPINION_SECONDARY + ')'

DOCKET_NUM = r'\bS\d+\b'


def normalize_whitespace(text):
    """Converts literal newlines ('\' followed by 'n') and whitespace (including Unicode) to a single space character.
    """
    return re.sub(r'(?:\\n|\s)+', ' ', text, flags=re.UNICODE)
