PRAGMA foreign_keys = ON;  -- For SQLite only. Off by default.

----- JUSTICES -----

CREATE TABLE justices (
    shorthand   VARCHAR(5)      PRIMARY KEY,
    short_name  VARCHAR(255)    UNIQUE          NOT NULL,
    fullname    VARCHAR(255)    UNIQUE          NOT NULL
);

----- CASE FILINGS -----

CREATE TABLE case_filings (
    docket_number   VARCHAR(255)    PRIMARY KEY,
    url             VARCHAR(255)                    NOT NULL,
    plain_text      CLOB                            NOT NULL,
-- TODO: Use to check for updates?
    sha1            VARCHAR(255)                    NOT NULL,
-- When the filing was officially filed.
    filed_on        DATE                            NOT NULL,
-- When the filing was added locally.
    added_on        TIMESTAMP                       NOT NULL    DEFAULT CURRENT_TIMESTAMP,
-- When official changes were last made made to the filing.
    modified_on     DATE                                        DEFAULT NULL,
-- When changes were last made locally.
    updated_on      TIMESTAMP                                   DEFAULT NULL,
    reviewer        VARCHAR(255)                                DEFAULT NULL,
    reviewed_on     TIMESTAMP                                   DEFAULT NULL
);

CREATE INDEX IDX_CaseFilings_PublishedOn
    ON case_filings (filed_on);

CREATE TRIGGER TR_CaseFilings_AfterUpdate
    AFTER UPDATE ON case_filings
    FOR EACH ROW
    WHEN OLD.updated_on IS NULL OR NEW.updated_on < OLD.updated_on  -- Prevents infinite recursion.
    BEGIN
        UPDATE case_filings
            SET updated_on = CURRENT_TIMESTAMP
            WHERE docket_number = OLD.docket_number;
    END;

----- OPINION TYPES -----

CREATE TABLE opinion_types (
    id      INTEGER         PRIMARY KEY,
    type    VARCHAR(255)    UNIQUE          NOT NULL
);

----- OPINIONS -----

CREATE TABLE opinions (
    id                          INTEGER         PRIMARY KEY                 AUTOINCREMENT,
    case_filing_docket_number   VARCHAR(255)                    NOT NULL,
    opinion_type_id             INTEGER                         NOT NULL,
    effective_op_type           INTEGER                         NOT NULL,
    authoring_justice           INTEGER                         NOT NULL,

    CONSTRAINT UQ_Opinions
        UNIQUE (case_filing_docket_number, opinion_type_id, authoring_justice),

    CONSTRAINT FK_Opinions_CaseFilings
        FOREIGN KEY (case_filing_docket_number)
        REFERENCES case_filings (docket_number),

    CONSTRAINT FK_Opinions_OpinionTypes
        FOREIGN KEY (opinion_type_id)
        REFERENCES opinion_types (id),

    CONSTRAINT FK_Opinions_OpinionTypes_effective
        FOREIGN KEY (effective_op_type)
        REFERENCES opinion_types (id),

    CONSTRAINT FK_Opinions_Justices
        FOREIGN KEY (authoring_justice)
        REFERENCES justices (shorthand)
);

CREATE INDEX IDX_Opinions_CaseFilingDocketNum
    ON opinions (case_filing_docket_number);

CREATE INDEX IDX_Opinions_OpinionTypeId
    ON opinions (opinion_type_id);

CREATE INDEX IDX_Opinions_OpinionTypeId_effective
    ON opinions (effective_op_type);

CREATE INDEX IDX_Opinions_AuthoringJustice
    ON opinions (authoring_justice);

----- CONCURRENCES -----

CREATE TABLE concurrences (
    id          INTEGER     PRIMARY KEY                 AUTOINCREMENT,
    opinion_id  INTEGER                     NOT NULL,
    justice     INTEGER                     NOT NULL,

    CONSTRAINT UQ_Concurrences
        UNIQUE (opinion_id, justice),

    CONSTRAINT FK_Concurrences_Opinions
        FOREIGN KEY (opinion_id)
        REFERENCES opinions (id),

    CONSTRAINT FK_Concurrences_Justices
        FOREIGN KEY (justice)
        REFERENCES justices (shorthand)
);

CREATE INDEX IDX_Concurrences_OpinionId
    ON concurrences (opinion_id);

CREATE INDEX IDX_Concurrences_Justice
    ON concurrences (justice);
