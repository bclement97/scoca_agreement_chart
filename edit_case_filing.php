<?php
require_once 'lib/db.php';
require_once 'lib/html.php';
require_once 'lib/opinions.php';

function get_case_filing(SQLite3 $db, $docket_number) {
    $stmt = $db->prepare(
        'SELECT 
            url, sha1, filed_on, added_on,
            ends_in_letter_flag, no_opinions_flag
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

function opinions_to_list($opinions) {
    global $opinion_types, $justices;

    if (sizeof($opinions) === 0) {
        return 'No opinions.';
    }

    $ul = '<ul class="no-bullet">';
    foreach ($opinions as $id => $opinion) {
        $type = strtoupper($opinion_types[$opinion['type_id']]);
        $justice = $justices[$opinion['authoring_justice']];
        $ul .= "<li>$type opinion by $justice</li>";
    }
    $ul .= '</ul>';
    return $ul;
}

$db = connect();

if (isset($_POST['docket_number'])) {
    $docket_number = $_POST['docket_number'];
    // TODO: update
} else if (isset($_GET['docket_number'])) {
    $docket_number = $_GET['docket_number'];
} else {
    $db->close();
    exit('Docket number is not set.');
}

$justices = get_justices($db);
$opinion_types = get_opinion_types($db);
$case_filing = get_case_filing($db, $docket_number);
if ($case_filing['ends_in_letter_flag'] === 1) {
    $alt_docket_number = substr($docket_number, 0, -1);
    $alt_case_filing = get_case_filing($db, $alt_docket_number);
} else {
    $alt_docket_number = $alt_case_filing = null;
}
$db->close();
?>

<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="edit.css">
</head>
<body>
    <h1>Case Filing <?=$docket_number?></h1>

    <form action="" method="post">
        <input type="hidden" name="docket_number" value="<?=$docket_number?>" />
        <table>
            <tr>
                <th>FLAGS: (check to clear)</th>
                <td>
                    <ul class="no-bullet">
                        <?php
                        if ($case_filing['ends_in_letter_flag'] === 1) echo '<li>' . flag_to_checkbox('ends_in_letter_flag') . '</li>';
                        if ($case_filing['no_opinions_flag'] === 1) echo '<li>' . flag_to_checkbox('no_opinions_flag') . '</li>';
                        ?>
                    </ul>
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

    <table>
        <tr>
            <th>URL:</th>
            <td>
                <a href="<?=$case_filing['url']?>" target="_blank">
                    <?=$case_filing['url']?>
                </a>
            </td>
        </tr>
        <tr>
            <th>SHA1:</th>
            <td>
                <?=$case_filing['sha1']?>
            </td>
        </tr>
        <tr>
            <th>FILED ON:</th>
            <td>
                <?=$case_filing['filed_on']?>
            </td>
        </tr>
        <tr>
            <th>ADDED ON:</th>
            <td>
                <?=$case_filing['added_on']?>
            </td>
        </tr>
        <tr>
            <th>OPINIONS:</th>
            <td>
                <?=opinions_to_list($case_filing['opinions'])?>
            </td>
        </tr>
    </table>

    <?php
    if (!is_null($alt_docket_number)) {
        if ($alt_case_filing === false) {
            echo "<h2>$alt_docket_number is not in the database.</h2>";
        } else {
            ?>
            <div class="alt-case-filing">
                <h2>Case Filing <?= $alt_docket_number ?></h2>

                <table>
                    <tr>
                        <th>URL:</th>
                        <td>
                            <a href="<?= $alt_case_filing['url'] ?>" target="_blank">
                                <?= $alt_case_filing['url'] ?>
                            </a>
                        </td>
                    </tr>
                    <tr>
                        <th>SHA1:</th>
                        <td>
                            <?= $alt_case_filing['sha1'] ?>
                        </td>
                    </tr>
                    <tr>
                        <th>FILED ON:</th>
                        <td>
                            <?= $alt_case_filing['filed_on'] ?>
                        </td>
                    </tr>
                    <tr>
                        <th>ADDED ON:</th>
                        <td>
                            <?= $alt_case_filing['added_on'] ?>
                        </td>
                    </tr>
                    <tr>
                        <th>OPINIONS:</th>
                        <td>
                            <?=opinions_to_list($alt_case_filing['opinions'])?>
                        </td>
                    </tr>
                </table>
            </div>
            <?php
        }
    }
    ?>
</body>
</html>
