<?php
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
