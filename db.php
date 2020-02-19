<?php
$db = new SQLite3('../.db');

function row_count(SQLite3Result $result) {
    $count = 0;
    while ($row = $result->fetchArray()) {
        ++$count;
    }
    $result->reset();
    return $count;
}

function result_to_table(SQLite3Result $result) {
    $table = '<table><thead>';
    for ($i = 0; $i < $result->numColumns(); ++$i) {
        $col_name = $result->columnName($i);
        $table .= "<th>$col_name</th>";
    }
    $table .= '</thead><tbody>';
    while ($row = $result->fetchArray(SQLITE3_NUM)) {
        $table .= '<tr>';
        foreach ($row as $val) {
            $table .= "<td>$val</td>";
        }
        $table .= '</tr>';
    }
    $table .= '</tbody></table>';
    return $table;
}
