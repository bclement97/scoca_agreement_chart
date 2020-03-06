<?php
function get_case_filing(SQLite3 $db, $docket_number) {
    $stmt = $db->prepare(
        'SELECT 
            url, sha1, filed_on, added_on,
            ends_in_letter_flag, no_opinions_flag, exclude_from_chart
        FROM case_filings
        WHERE docket_number = :docket_number'
    );
    $stmt->bindValue(':docket_number', $docket_number);
    $row = $stmt->execute()->fetchArray(SQLITE3_ASSOC);
    if ($row !== false) {
        $row['docket_number'] = $docket_number;
        $row['opinions'] = get_opinions($db, $docket_number);
    }
    return $row;
}

function get_opinion(SQLite3 $db, $id) {
    $stmt = $db->prepare(
        'SELECT 
            o.id, o.docket_number, o.type_id, o.effective_type_id, 
            o.authoring_justice, o.effective_type_flag, o.no_concurrences_flag,
            cf.url
        FROM opinions o
        JOIN case_filings cf ON o.docket_number = cf.docket_number
        WHERE id = :id'
    );
    $stmt->bindValue(':id', $id);
    $row = $stmt->execute()->fetchArray(SQLITE3_ASSOC);
    $row['concurring_justices'] = get_concurrences($db, $id);
    return $row;
}

function get_opinions(SQLite3 $db, $docket_number) {
    $stmt = $db->prepare(
        'SELECT id, type_id, authoring_justice
        FROM opinions
        WHERE docket_number = :docket_number'
    );
    $stmt->bindValue(':docket_number', $docket_number);
    $result = $stmt->execute();
    $opinions = array();
    while (($row = $result->fetchArray(SQLITE3_ASSOC)) !== false) {
        $opinions[$row['id']] = $row;
    }
    return $opinions;
}

function get_concurrences(SQLite3 $db, $opinion_id) {
    $stmt = $db->prepare('SELECT justice FROM concurrences WHERE opinion_id = :id');
    $stmt->bindValue(':id', $opinion_id);
    $result = $stmt->execute();
    $justices = array();
    while (($row = $result->fetchArray(SQLITE3_ASSOC)) !== false) {
        $justices[] = $row['justice'];
    }
    return $justices;
}

function get_opinion_types(SQLite3 $db) {
    $result = $db->query('SELECT id, type FROM opinion_types');
    $opinion_types = array();
    while (($row = $result->fetchArray(SQLITE3_ASSOC)) !== false) {
        $opinion_types[$row['id']] = $row['type'];
    }
    return $opinion_types;
}

function get_justices(SQLite3 $db) {
    $result = $db->query('SELECT shorthand, fullname FROM justices');
    $justices = array();
    while (($row = $result->fetchArray(SQLITE3_ASSOC)) !== false) {
        $justices[$row['shorthand']] = $row['fullname'];
    }
    return $justices;
}
