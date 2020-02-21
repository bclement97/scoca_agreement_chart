<?php
require_once 'db.php';

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
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $justices[] = $row['justice'];
    }
    return $justices;
}

function get_justices(SQLite3 $db) {
    $result = $db->query('SELECT shorthand, fullname FROM justices');
    $justices = array();
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $justices[$row['shorthand']] = $row['fullname'];
    }
    return $justices;
}

function get_opinion_types(SQLite3 $db) {
    $result = $db->query('SELECT id, type FROM opinion_types');
    $opinion_types = array();
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $opinion_types[$row['id']] = $row['type'];
    }
    return $opinion_types;
}

function update_opinion(SQLite3 $db, $post) {
    $sql = 'UPDATE opinions SET
                type_id = :type_id,
                effective_type_id = :effective_type_id,
                authoring_justice = :authoring_justice';
    if (isset($post['effective_type_flag'])) {
        $sql .= ', effective_type_flag = :effective_type_flag';
    }
    if (isset($post['no_concurrences_flag'])) {
        $sql .= ', no_concurrences_flag = :no_concurrences_flag';
    }
    $sql .= ' WHERE id = :id';

    $stmt = $db->prepare($sql);

    $stmt->bindValue(':type_id', $post['type_id']);
    $stmt->bindValue(':effective_type_id', $post['effective_type_id']);
    $stmt->bindValue(':authoring_justice', $post['authoring_justice']);
    if (isset($post['effective_type_flag'])) {
        $stmt->bindValue(':effective_type_flag', $post['effective_type_flag']);
    }
    if (isset($post['no_concurrences_flag'])) {
        $stmt->bindValue(':no_concurrences_flag', $post['no_concurrences_flag']);
    }
    $stmt->bindValue(':id', $post['id']);

    $stmt->execute();
}


function update_concurrences(SQLite3 $db, $opinion_id, $new_justices, $old_justices) {
    sort($new_justices);
    sort($old_justices);
    if ($new_justices === $old_justices) {
        // Nothing to update.
        return;
    }

    $delete_stmt = $db->prepare('DELETE FROM concurrences WHERE opinion_id = :id AND justice = :justice');
    foreach (array_diff($old_justices, $new_justices) as $justice) {
        $delete_stmt->bindValue(':id', $opinion_id);
        $delete_stmt->bindValue(':justice', $justice);
        $delete_stmt->execute();
        $delete_stmt->reset();
    }

    $insert_stmt = $db->prepare('INSERT INTO concurrences (opinion_id, justice) VALUES (:id, :justice)');
    foreach (array_diff($new_justices, $old_justices) as $justice) {
        $insert_stmt->bindValue(':id', $opinion_id);
        $insert_stmt->bindValue(':justice', $justice);
        $insert_stmt->execute();
        $insert_stmt->reset();
    }
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

if (isset($_GET['id'])) {
    $id = $_GET['id'];
} else {
    echo 'ID is not set.';
    die();
}

if (isset($_POST['id'])) {
    if ($_POST['id'] !== $id) {
        echo '<p>ERROR: IDs provided by GET and POST do not match.</p>';
    } else if (!isset($_POST['type_id'], $_POST['effective_type_id'], $_POST['authoring_justice'])) {
        echo '<p>ERROR: Could not update, a required field is missing</p><pre>';
        print_r($_POST);
        echo '</pre>';
    } else {
        $new_concurrences = isset($_POST['concurring_justices']) ? $_POST['concurring_justices'] : array();
        $old_concurrences = get_concurrences($db, $id);

        $db->exec('BEGIN');
        update_opinion($db, $_POST);
        update_concurrences($db, $id, $new_concurrences, $old_concurrences);
        $db->exec('COMMIT');
    }
}

$justices = get_justices($db);
$opinion_types = get_opinion_types($db);
$opinion = get_opinion($db, $id);
?>

<h1>Opinion #<?=$id?> (<?=$opinion['docket_number']?>)</h1>
<h2><?=strtoupper($opinion_types[$opinion['type_id']])?> opinion by <?=$justices[$opinion['authoring_justice']]?></h2>

<p>
    <a href="<?=$opinion['url']?>" target="_blank">View <?=$opinion['docket_number']?> on CourtListener</a>
</p>

<form action="" method="post">
    <input type="hidden" name="id" value="<?=$id?>" />
    <div>
        FLAGS: (check to clear)
        <ul>
            <?php
            if ($opinion['effective_type_flag'] === 1) echo '<li>' . flag_to_checkbox('effective_type_flag') . '</li>';
            if ($opinion['no_concurrences_flag'] === 1) echo '<li>' . flag_to_checkbox('no_concurrences_flag') . '</li>';
            ?>
        </ul>
    </div>
    <div>
        TYPE:
        <?=array_to_select($opinion_types, 'type_id', $opinion['type_id'])?>
    </div>
    <div>
        EFFECTIVE TYPE:
        <?=array_to_select($opinion_types, 'effective_type_id', $opinion['effective_type_id'])?>
        (ignored when TYPE is <strong>NOT</strong> concurring and dissenting)</div>
    <div>
        AUTHORING JUSTICE:
        <?=array_to_select($justices, 'authoring_justice', $opinion['authoring_justice'])?>
    </div>
    <div>
        CONCURRING JUSTICE(S):
        <?=array_to_select($justices, 'concurring_justices', $opinion['concurring_justices'], true)?>
        (if AUTHORING JUSTICE is selected, it will be ignored)
    </div>
    <div>
        <input type="submit" value="Submit" />
        <input type="reset" value="Reset" />
    </div>
</form>
