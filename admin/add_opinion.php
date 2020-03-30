<?php
require_once 'lib/db.php';
require_once 'lib/html.php';
require_once 'lib/models.php';

function add_opinion(SQLite3 $db, $post) {
    // Only set the effective type when it's a concurring and dissenting opinion.
    $effective_type_id = $post['type_id'] === '4' ? $post['effective_type_id'] : null;

    $insert_stmt = $db->prepare(
        'INSERT INTO opinions (
            docket_number, type_id, effective_type_id, authoring_justice,
            effective_type_flag, no_concurrences_flag
        ) VALUES (
            :docket_number, :type_id, :effective_type_id, :authoring_justice,
            :effective_type_flag, :no_concurrences_flag
        )'
    );
    $insert_stmt->bindValue(':docket_number', $post['docket_number']);
    $insert_stmt->bindValue(':type_id', $post['type_id']);
    $insert_stmt->bindValue(':effective_type_id', $effective_type_id);
    $insert_stmt->bindValue(':authoring_justice', $post['authoring_justice']);
    $insert_stmt->bindValue(':effective_type_flag', $post['effective_type_flag']);
    $insert_stmt->bindValue(':no_concurrences_flag', $post['no_concurrences_flag']);
    $insert_stmt->execute();

    $select_stmt = $db->prepare(
        'SELECT id FROM opinions WHERE 
            docket_number = :docket_number
            AND type_id = :type_id
            AND authoring_justice = :authoring_justice'
    );
    $select_stmt->bindValue(':docket_number', $post['docket_number']);
    $select_stmt->bindValue(':type_id', $post['type_id']);
    $select_stmt->bindValue(':authoring_justice', $post['authoring_justice']);
    $result = $select_stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);
    return $row['id'];
}

function add_concurrences(SQLite3 $db, $opinion_id, $concurrences) {
    $stmt = $db->prepare('INSERT INTO concurrences (opinion_id, justice) VALUES (:id, :justice)');
    foreach ($concurrences as $justice) {
        $stmt->bindValue(':id', $opinion_id);
        $stmt->bindValue(':justice', $justice);
        $stmt->execute();
        $stmt->reset();
    }
}

$db = connect();

if (isset($_POST['docket_number'])) {
    $docket_number = $_POST['docket_number'];

    if (!isset($_POST['type_id'], $_POST['effective_type_id'], $_POST['authoring_justice'],
        $_POST['effective_type_flag'], $_POST['no_concurrences_flag'])) {
        echo '<p>ERROR: Could not update, a required field is missing</p><pre>';
        print_r($_POST);
        echo '</pre>';
    } else {
        $concurrences = isset($_POST['concurring_justices']) ? $_POST['concurring_justices'] : array();
        // The authoring justice can't concur with themselves.
        if (($key = array_search($_POST['authoring_justice'], $concurrences)) !== false) {
            unset($concurrences[$key]);
        }

        $id = add_opinion($db, $_POST);
        $db->exec('BEGIN TRANSACTION');
        add_concurrences($db, $id, $concurrences);
        $db->exec('COMMIT TRANSACTION');

        // header($_SERVER['SERVER_PROTOCOL'] . ' 201 Created');
        header("Location: edit_case_filing.php?docket_number=$docket_number");
        exit();
    }
} else if (isset($_GET['docket_number'])) {
    $docket_number = $_GET['docket_number'];
} else {
    $db->close();
    exit('Docket number is not set.');
}

$justices = get_justices($db);
$opinion_types = get_opinion_types($db);
?>

<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="styles/edit.css">
</head>
<body>
    <h1>New Opinion for <?=$docket_number?></h1>

    <p>
        <a href="edit_case_filing.php?docket_number=<?=$docket_number?>">Back to <?=$docket_number?></a><br />
        <a href="index.php">Back to Flagged Case Filings/Opinions</a>
    </p>

    <form action="" method="post">
        <input type="hidden" name="docket_number" value="<?=$docket_number?>" />
        <table>
            <tr>
                <th>FLAGS:</th>
                <td>
                    <table>
                        <?php
                        echo flags_to_rows(null, 'effective_type_flag', 'no_concurrences_flag');
                        ?>
                    </table>
                </td>
            </tr>
            <tr>
                <th>TYPE:</th>
                <td>
                    <?=array_to_select($opinion_types, 'type_id')?>
                </td>
            </tr>
            <tr>
                <th>EFFECTIVE TYPE:</th>
                <td>
                    <?=array_to_select($opinion_types, 'effective_type_id')?>
                    (ignored when TYPE is <strong>NOT</strong> concurring and dissenting)
                </td>
            </tr>
            <tr>
                <th>AUTHORING JUSTICE:</th>
                <td>
                    <?=array_to_select($justices, 'authoring_justice')?>
                </td>
            </tr>
            <tr>
                <th>CONCURRING JUSTICE(S):</th>
                <td>
                    <?=array_to_select($justices, 'concurring_justices', [], true)?>
                    (if AUTHORING JUSTICE is selected, it will be ignored)
                </td>
            </tr>
            <tr>
                <td></td>
                <td>
                    <input type="submit" value="Add" />
                    <input type="reset" value="Reset" />
                </td>
            </tr>
        </table>
    </form>
</body>
</html>
