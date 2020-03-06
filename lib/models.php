<?php
/** Helper functions for getting array objects analogous to the models of the CLI. */

/**
 * @param \SQLite3 $db The database connection.
 * @param string   $docket_number The docket number of the case filing to get.
 *
 * @return array|false The case filing as an array, or false if no case filing exists under DOCKET_NUMBER.
 */
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

/**
 * @param \SQLite3   $db The database connection.
 * @param integer    $id The ID of the opinion to get.
 *
 * @return array|false The opinion as an array, or false if no opinion exists under ID.
 */
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

/**
 * @param \SQLite3 $db The database connection.
 * @param string   $docket_number The docket number of the case filing for which to get all opinions.
 *
 * @return array An array of opinions indexed by opinion ID.
 */
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

/**
 * @param \SQLite3   $db The database connection.
 * @param integer    $opinion_id The opinion ID for which to get concurrences.
 *
 * @return array An array of justice IDs who concur with the opinion.
 */
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

/**
 * @param \SQLite3 $db The database connection.
 *
 * @return array An array of ID => Opinion type string
 */
function get_opinion_types(SQLite3 $db) {
    $result = $db->query('SELECT id, type FROM opinion_types');
    $opinion_types = array();
    while (($row = $result->fetchArray(SQLITE3_ASSOC)) !== false) {
        $opinion_types[$row['id']] = $row['type'];
    }
    return $opinion_types;
}

/**
 * @param \SQLite3 $db The database connection.
 *
 * @return array An array of SHORTHAND => FULLNAME.
 */
function get_justices(SQLite3 $db) {
    $result = $db->query('SELECT shorthand, fullname FROM justices');
    $justices = array();
    while (($row = $result->fetchArray(SQLITE3_ASSOC)) !== false) {
        $justices[$row['shorthand']] = $row['fullname'];
    }
    return $justices;
}
