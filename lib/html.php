<?php
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

function array_to_select($arr, $name, $selected = null, $multi = false) {
    assert(is_array($selected) === $multi);

    $select = '<select ';
    if ($multi) {
        $name .= '[]'; // Allows all selected values to be submitted.
        $select .= 'size="' . sizeof($arr) . '" multiple ';
    }
    $select .= "name='$name'>";
    foreach ($arr as $key => $val) {
        $select .= "<option value='$key'";
        if ($selected !== null && (($multi && in_array($key, $selected, true)) || $selected === $key)) {
            $select .= ' selected';
        }
        $select .= ">$key - $val</option>";
    }
    $select .= '</select>';
    return $select;
}

function flag_to_checkbox($flag) {
    return "<input type='checkbox' name='$flag' value='0' /> $flag";
}

function flag_to_radio($flag, $value) {
    $radio = "<input type='radio' name='$flag' value='1'";
    if ($value === 1) $radio .= ' checked';
    $radio .= " /> Set <input type='radio' name='$flag' value='0'";
    if ($value === 0) $radio .= ' checked';
    $radio .= " /> Unset";
    return $radio;
}

