CREATE TABLE justices (
    id          INTEGER         PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(255)    UNIQUE      NOT NULL,
    shorthand   VARCHAR(5)      UNIQUE      NOT NULL
);

CREATE TABLE case_filings (
    docket_num      VARCHAR(255)    PRIMARY KEY,
    url             VARCHAR(255)    UNIQUE          NOT NULL,
    plain_text      CLOB            NOT NULL,
    plain_text_hash CHAR(64)        UNIQUE          NOT NULL,
    published_on    DATE            NOT NULL,
    added_on        DATE            NOT NULL        DEFAULT CURRENT_TIMESTAMP,
    updated_on      DATE            DEFAULT NULL,
    reviewer        VARCHAR(255)    DEFAULT NULL,
    reviewed_on     TIMESTAMP       DEFAULT NULL
);

CREATE TABLE opinion_types (
    id      INTEGER         PRIMARY KEY AUTOINCREMENT,
    type    VARCHAR(255)    UNIQUE      NOT NULL
);
INSERT INTO opinion_types(type) VALUES ('Majority');
INSERT INTO opinion_types(type) VALUES ('Concurring');
INSERT INTO opinion_types(type) VALUES ('Dissenting');
INSERT INTO opinion_types(type) VALUES ('Concurring and Dissenting');

CREATE TABLE opinions (
    id                      INTEGER         PRIMARY KEY AUTOINCREMENT,
    case_filing_docket_num  VARCHAR(255)    NOT NULL,
    opinion_type_id         INTEGER         NOT NULL,
    authoring_justice_id    INTEGER         NOT NULL,

    CONSTRAINT FK_Opinion_CaseFiling FOREIGN KEY (case_filing_docket_num)
        REFERENCES case_filings(docket_num),
    CONSTRAINT FK_Opinion_OpinionType FOREIGN KEY (opinion_type_id)
        REFERENCES opinion_types(id),
    CONSTRAINT FK_Opinion_Justice FOREIGN KEY (authoring_justice_id)
        REFERENCES justices(id)
);

CREATE TABLE concurrences (
    id          INTEGER     PRIMARY KEY AUTOINCREMENT,
    opinion_id  INTEGER     NOT NULL,
    justice_id  INTEGER     NOT NULL,

    CONSTRAINT FK_Concurrence_Opinion FOREIGN KEY (opinion_id)
        REFERENCES opinions(id),
    CONSTRAINT FK_Concurrence_Justice FOREIGN KEY (justice_id)
        REFERENCES justices(id)
);