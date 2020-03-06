<?php
require_once 'lib/db.php';
require_once 'lib/html.php';
require_once 'lib/opinions.php';

function update_opinion(SQLite3 $db, $post) {
    // Only set the effective type when it's a concurring and dissenting opinion.
    $effective_type_id = $post['type_id'] === '4' ? $post['effective_type_id'] : null;

    $stmt = $db->prepare(
        'UPDATE opinions SET
            type_id = :type_id,
            effective_type_id = :effective_type_id,
            authoring_justice = :authoring_justice,
            effective_type_flag = :effective_type_flag,
            no_concurrences_flag = :no_concurrences_flag
        WHERE id = :id'
    );
    $stmt->bindValue(':type_id', $post['type_id']);
    $stmt->bindValue(':effective_type_id', $effective_type_id);
    $stmt->bindValue(':authoring_justice', $post['authoring_justice']);
    $stmt->bindValue(':effective_type_flag', $post['effective_type_flag']);
    $stmt->bindValue(':no_concurrences_flag', $post['no_concurrences_flag']);
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

$db = connect();

if (isset($_POST['id'])) {
    $id = $_POST['id'];

    if (!isset($_POST['type_id'], $_POST['effective_type_id'], $_POST['authoring_justice'],
               $_POST['effective_type_flag'], $_POST['no_concurrences_flag'])) {
        echo '<p>ERROR: Could not update, a required field is missing</p><pre>';
        print_r($_POST);
        echo '</pre>';
    } else {
        $old_concurrences = get_concurrences($db, $id);
        $new_concurrences = isset($_POST['concurring_justices']) ? $_POST['concurring_justices'] : array();
        // The authoring justice can't concur with themselves.
        if (($key = array_search($_POST['authoring_justice'], $new_concurrences)) !== false) {
            unset($new_concurrences[$key]);
        }

        $db->exec('BEGIN TRANSACTION');
        update_opinion($db, $_POST);
        update_concurrences($db, $id, $new_concurrences, $old_concurrences);
        $db->exec('COMMIT TRANSACTION');
    }
} else if (isset($_GET['id'])) {
    $id = $_GET['id'];
} else {
    $db->close();
    exit('ID is not set.');
}

$justices = get_justices($db);
$opinion_types = get_opinion_types($db);
$opinion = get_opinion($db, $id);
$db->close();
?>

<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="styles/edit.css">
</head>
<body>
    <h1>Opinion #<?=$id?> (<?=$opinion['docket_number']?>)</h1>
    <h2><?=strtoupper($opinion_types[$opinion['type_id']])?> opinion by <?=$justices[$opinion['authoring_justice']]?></h2>

    <p>
        <a href="<?=$opinion['url']?>" target="_blank">View <?=$opinion['docket_number']?> on CourtListener</a>
    </p>

    <form action="" method="post">
        <input type="hidden" name="id" value="<?=$id?>" />
        <table>
            <tr>
                <th>FLAGS:</th>
                <td>
                    <table>
                        <?php
                        echo flags_to_rows($opinion, 'effective_type_flag', 'no_concurrences_flag');
                        ?>
                    </table>
                </td>
            </tr>
            <tr>
                <th>TYPE:</th>
                <td>
                    <?=array_to_select($opinion_types, 'type_id', $opinion['type_id'])?>
                </td>
            </tr>
            <tr>
                <th>EFFECTIVE TYPE:</th>
                <td>
                    <?=array_to_select($opinion_types, 'effective_type_id', $opinion['effective_type_id'])?>
                    (ignored when TYPE is <strong>NOT</strong> concurring and dissenting)
                </td>
            </tr>
            <tr>
                <th>AUTHORING JUSTICE:</th>
                <td>
                    <?=array_to_select($justices, 'authoring_justice', $opinion['authoring_justice'])?>
                </td>
            </tr>
            <tr>
                <th>CONCURRING JUSTICE(S):</th>
                <td>
                    <?=array_to_select($justices, 'concurring_justices', $opinion['concurring_justices'], true)?>
                    (if AUTHORING JUSTICE is selected, it will be ignored)
                </td>
            </tr>
            <tr>
                <td></td>
                <td>
                    <input type="submit" value="Submit" />
                    <input type="reset" value="Reset" />
                </td>
            </tr>
        </table>
    </form>
</body>
</html>
