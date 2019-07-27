PRAGMA foreign_keys = ON;  -- For SQLite only. Off by default.

----- JUSTICES -----

CREATE TABLE justices (
    id          INTEGER         PRIMARY KEY                 AUTOINCREMENT,
    name        VARCHAR(255)    UNIQUE          NOT NULL,
    shorthand   VARCHAR(5)      UNIQUE          NOT NULL
);

----- CASE FILINGS -----

CREATE TABLE case_filings (
    docket_number   VARCHAR(255)    PRIMARY KEY,
    url             VARCHAR(255)                    NOT NULL,
    plain_text      CLOB                            NOT NULL,
-- TODO: Use to check for updates?
    plain_text_hash VARCHAR(255)                    NOT NULL,
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
    ON case_filings(filed_on);

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

-- TODO: Move to Python module setup/init?
INSERT INTO opinion_types VALUES (0, 'Majority');
INSERT INTO opinion_types VALUES (1, 'Concurring');
INSERT INTO opinion_types VALUES (2, 'Dissenting');
INSERT INTO opinion_types VALUES (3, 'Concurring and Dissenting');

----- OPINIONS -----

CREATE TABLE opinions (
    id                          INTEGER         PRIMARY KEY                 AUTOINCREMENT,
    case_filing_docket_number   VARCHAR(255)                    NOT NULL,
    opinion_type_id             INTEGER                         NOT NULL,
    authoring_justice_id        INTEGER                         NOT NULL,

    CONSTRAINT UQ_Opinions
        UNIQUE (case_filing_docket_number, opinion_type_id, authoring_justice_id),

    CONSTRAINT FK_Opinions_CaseFilings
        FOREIGN KEY (case_filing_docket_number)
        REFERENCES case_filings(docket_number),

    CONSTRAINT FK_Opinions_OpinionTypes
        FOREIGN KEY (opinion_type_id)
        REFERENCES opinion_types(id),

    CONSTRAINT FK_Opinions_Justices
        FOREIGN KEY (authoring_justice_id)
        REFERENCES justices(id)
);

CREATE INDEX IDX_Opinions_CaseFilingDocketNum
    ON opinions(case_filing_docket_number);

CREATE INDEX IDX_Opinions_OpinionTypeId
    ON opinions(opinion_type_id);

CREATE INDEX IDX_Opinions_AuthoringJusticeId
    ON opinions(authoring_justice_id);

----- CONCURRENCES -----

CREATE TABLE concurrences (
    id          INTEGER     PRIMARY KEY                 AUTOINCREMENT,
    opinion_id  INTEGER                     NOT NULL,
    justice_id  INTEGER                     NOT NULL,

    CONSTRAINT UQ_Concurrences
        UNIQUE (opinion_id, justice_id),

    CONSTRAINT FK_Concurrences_Opinions
        FOREIGN KEY (opinion_id)
        REFERENCES opinions(id),

    CONSTRAINT FK_Concurrences_Justices
        FOREIGN KEY (justice_id)
        REFERENCES justices(id)
);

CREATE INDEX IDX_Concurrences_OpinionId
    ON concurrences(opinion_id);

CREATE INDEX IDX_Concurrences_JusticeId
    ON concurrences(justice_id);
