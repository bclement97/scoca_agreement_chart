<?php
$db = new SQLite3('../.db');

function row_count(SQLite3Result $result) {
    $count = 0;
    while (($row = $result->fetchArray()) !== false) ++$count;
    $result->reset();
    return $count;
}

function result_to_table(SQLite3Result $result, $edit = null, $id_col = null) {
    assert(is_null($edit) === is_null($id_col));

    $table = '<table><thead>';
    for ($i = 0; $i < $result->numColumns(); ++$i) {
        $col_name = $result->columnName($i);
        $table .= "<th>$col_name</th>";
    }
    $table .= '</thead><tbody>';
    while (($row = $result->fetchArray(SQLITE3_ASSOC)) !== false) {
        $table .= '<tr>';
        foreach ($row as $col => $val) {
            if ($val === null) $val = "NULL";
            if ($edit !== null && $col === $id_col) {
                $uri = sprintf($edit, $id_col, $val);
                $table .= "<td><a href='$uri'>$val</a></td>";
            } else {
                $table .= "<td>$val</td>";
            }
        }
        $table .= '</tr>';
    }
    $table .= '</tbody></table>';
    return $table;
}
