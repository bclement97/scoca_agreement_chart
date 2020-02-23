<?php
require_once 'db.php';

function get_case_filing(SQLite3 $db, $docket_number) {
    $stmt = $db->prepare(
        'SELECT 
            url, sha1, filed_on, added_on,
            ends_in_letter_flag, no_opinions_flag
        FROM case_filings
        WHERE docket_number = :docket_number'
    );
    $stmt->bindValue(':docket_number', $docket_number);
    $row = $stmt->execute()->fetchArray(SQLITE3_ASSOC);
    $row['docket_number'] = $docket_number;
    return $row;
}
