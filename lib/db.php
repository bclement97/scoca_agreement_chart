<?php
/** Database functions. */

/**
 * @param string $db_file Optional. Where the SQLite3 database file is located.
 *
 * @return \SQLite3 A new SQLite3 connection.
 */
function connect($db_file = null) {
    if (is_null($db_file)) {
        $db_file = dirname(dirname(__DIR__)) . '/.db';
    }
    return new SQLite3($db_file);
}

/**
 * @param \SQLite3Result $result The SQLite3Result for which to count rows.
 *
 * @return int The number of rows in RESULT.
 */
function row_count(SQLite3Result $result) {
    $count = 0;
    while (($row = $result->fetchArray()) !== false) ++$count;
    $result->reset();
    return $count;
}
