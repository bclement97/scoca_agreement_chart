DOCKET_NUM = r'\bS\d+\b'

"""
It is recommended to always use OPINION_REGEX with re.findall() or re.finditer() since it will always match
OPINION_REGEX_MAJORITY before matching OPINION_REGEX_SECONDARY. If not, matches of OPINION_REGEX_MAJORITY must be
removed from the search string before attempting to match OPINION_REGEX_SECONDARY which can wrongly include what should
be matched by OPINION_REGEX_MAJORITY.

The unicode and case-insensitive flag should be set in most cases. This is because this regex may not always match due
to typos, or minor differences in punctuation and encoded characters between published opinions and may need to be
updated accordingly and/or handled manually.
"""
_S = r'(?:\\n|\s)+'
_JUSTICE = r'Justice' + _S + '([^.,]*?)'
# Matches and returns the name of the authoring Justice of the opinion.
_OPINION_AUTHOR = r'(?:Chief )?Justice (.*?) (?:authored|filed) '
# Matches and returns the name(s) of the Justice(s) who concur(s) with an opinion.
# A match with multiple Justices should be in the form of 'X and Y' or 'X, Y, [...] and Z'.
_OPINION_CONCURRING = r',? in which (?:Chief Justice (.*?) and )?Justices? (.*?) concurred'
# Matches and returns the names of the authoring Justice of the majority opinion and those who concur with it.
OPINION_MAJORITY = _OPINION_AUTHOR + 'the opinion of the court' + _OPINION_CONCURRING
# Like OPINION_REGEX_MAJORITY, except for all other opinions.
OPINION_SECONDARY = _OPINION_AUTHOR + 'a (concurring|dissenting|concurring and dissenting) opinion' \
                          '(?:' + _OPINION_CONCURRING + ')?'
# Matches OPINION_REGEX_MAJORITY first and then OPINION_REGEX_SECONDARY.
OPINION = r'(?:' + OPINION_MAJORITY + ')|(?:' + OPINION_SECONDARY + ')'
