<?php
/** Helper functions for generating HTML to output. */

/**
 * @param \SQLite3Result $result The result to put into tabular form.
 * @param string $edit_href Optional, except when ID_COL is present. The href to the edit page for a given row.
 *                          Must contain two (2) '%s': the first is replaced by ID_COL and the second with the value of
 *                          ID_COL for the given row.
 * @param string $id_col    Optional, except when EDIT_HREF is present. The identifying column for a given row in
 *                          RESULT.
 *
 * @return string The RESULT in tabular form.
 */
function result_to_table(SQLite3Result $result, $edit_href = null, $id_col = null) {
    assert(is_null($edit_href) === is_null($id_col));

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
            if ($edit_href !== null && $col === $id_col) {
                $uri = sprintf($edit_href, $id_col, $val);
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

/**
 * @param array  $arr The array to display as a select box.
 * @param string $name The form name of the select box.
 * @param mixed $selected Optional. A key or, if MULTI is true, an array of keys of ARR that are to be selected by
 *                        default.
 * @param bool   $multi Optional. If the select box allows multiple values to be selected.
 *
 * @return string ARR as a select box.
 */
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

/**
 * @param string $flag The flag name.
 * @param string $value The current value of the flag.
 *
 * @return string The flag as two radio buttons with the current value checked.
 */
function flag_to_radio($flag, $value) {
    $radio = "<input type='radio' name='$flag' value='1'";
    if ($value === 1) $radio .= ' checked';
    $radio .= " /> Set <input type='radio' name='$flag' value='0'";
    if ($value === 0) $radio .= ' checked';
    $radio .= " /> Unset";
    return $radio;
}

/**
 * @param array  $obj An array of object values. Usually just a fetched array of a SQLite3Result object.
 * @param string ...$flags The flags for the given OBJ.
 *
 * @return string A TR row for each FLAGS as two radio buttons ({@see flag_to_radio()}).
 */
function flags_to_rows( /* $obj, ...$flags */ ) {
    $args = func_get_args();
    $obj = $args[0];
    $flags = array_slice($args, 1);

    $rows = '';
    foreach ($flags as $flag) {
        $radio = flag_to_radio($flag, $obj[$flag]);
        $rows .= "<tr><td>$flag</td><td>$radio</td></tr>";
    }
    return $rows;
}

