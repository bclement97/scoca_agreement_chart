PRAGMA foreign_keys = ON;  -- For SQLite only.

CREATE TABLE justices (
    id          INTEGER         PRIMARY KEY             AUTOINCREMENT,
    name        VARCHAR(255)    UNIQUE      NOT NULL,
    shorthand   VARCHAR(5)      UNIQUE      NOT NULL
);

CREATE TABLE case_filings (
    docket_num      VARCHAR(255)    PRIMARY KEY,
    url             VARCHAR(255)    UNIQUE          NOT NULL,
    plain_text      CLOB                            NOT NULL,
-- Use to check for updates?
    plain_text_hash CHAR(64)        UNIQUE          NOT NULL,
-- When the filing was officially published.
    published_on    DATE                            NOT NULL,
-- When the filing was added locally.
    added_on        TIMESTAMP                       NOT NULL    DEFAULT CURRENT_TIMESTAMP,
-- When official changes were made made to the filing.
    modified_on     DATE                                        DEFAULT NULL,
-- When official changes were updated locally.
    updated_on      TIMESTAMP                                   DEFAULT NULL,
    reviewer        VARCHAR(255)                                DEFAULT NULL,
    reviewed_on     TIMESTAMP                                   DEFAULT NULL
);
CREATE INDEX IDX_CaseFilings_PublishedOn ON case_filings(published_on);

CREATE TABLE opinion_types (
    id      INTEGER         PRIMARY KEY,
    type    VARCHAR(255)    UNIQUE      NOT NULL
);
INSERT INTO opinion_types VALUES (0, 'Majority');
INSERT INTO opinion_types VALUES (1, 'Concurring');
INSERT INTO opinion_types VALUES (2, 'Dissenting');
INSERT INTO opinion_types VALUES (3, 'Concurring and Dissenting');

CREATE TABLE opinions (
    id                      INTEGER         PRIMARY KEY             AUTOINCREMENT,
    case_filing_docket_num  VARCHAR(255)                NOT NULL,
    opinion_type_id         INTEGER                     NOT NULL,
    authoring_justice_id    INTEGER                     NOT NULL,

    CONSTRAINT FK_Opinion_CaseFiling FOREIGN KEY (case_filing_docket_num)
        REFERENCES case_filings(docket_num),
    CONSTRAINT FK_Opinion_OpinionType FOREIGN KEY (opinion_type_id)
        REFERENCES opinion_types(id),
    CONSTRAINT FK_Opinion_Justice FOREIGN KEY (authoring_justice_id)
        REFERENCES justices(id)
);
CREATE INDEX IDX_Opinions_CaseFilingDocketNum ON opinions(case_filing_docket_num);
CREATE INDEX IDX_Opinions_OpinionTypeId ON opinions(opinion_type_id);
CREATE INDEX IDX_Opinions_AuthoringJusticeId ON opinions(authoring_justice_id);

CREATE TABLE concurrences (
    id          INTEGER     PRIMARY KEY             AUTOINCREMENT,
    opinion_id  INTEGER                 NOT NULL,
    justice_id  INTEGER                 NOT NULL,

    CONSTRAINT FK_Concurrence_Opinion FOREIGN KEY (opinion_id)
        REFERENCES opinions(id),
    CONSTRAINT FK_Concurrence_Justice FOREIGN KEY (justice_id)
        REFERENCES justices(id)
);
CREATE INDEX IDX_Concurrences_OpinionId ON concurrences(opinion_id);
CREATE INDEX IDX_Concurrences_AuthoringJusticeId ON concurrences(justice_id);
