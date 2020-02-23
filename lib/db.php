<?php
function connect($db_file = null) {
    if (is_null($db_file)) {
        $db_file = dirname(dirname(__DIR__)) . '/.db';
    }
    return new SQLite3($db_file);
}

function row_count(SQLite3Result $result) {
    $count = 0;
    while (($row = $result->fetchArray()) !== false) ++$count;
    $result->reset();
    return $count;
}
