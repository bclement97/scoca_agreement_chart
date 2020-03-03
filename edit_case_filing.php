<?php
require_once 'lib/db.php';
require_once 'lib/html.php';
require_once 'lib/opinions.php';

function get_case_filing(SQLite3 $db, $docket_number) {
    $stmt = $db->prepare(
        'SELECT 
            url, sha1, filed_on, added_on,
            ends_in_letter_flag, no_opinions_flag, exclude_from_chart
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
        $ul .= "<li><a href='edit_opinion.php?id=$id' target='_blank'>($id) $type opinion by $justice</a></li>";
    }
    $ul .= '</ul>';
    return $ul;
}

function print_case_filing($case_filing, $is_alt = false) {
    echo (!$is_alt ? '<h1>' : '<h2>');
    echo "Case Filing {$case_filing['docket_number']}";
    echo (!$is_alt ? '</h1>' : '</h2>');
    ?>
    <table>
        <tr>
            <th>FLAGS:</th>
            <td>
                <form action="" method="post">
                    <input type="hidden" name="docket_number" value="<?=$case_filing['docket_number']?>" />
                    <table>
                        <?php
                        foreach (['exclude_from_chart', 'ends_in_letter_flag', 'no_opinions_flag'] as $flag) {
                            ?>
                            <tr>
                                <td><?=$flag?></td>
                                <td><?=flag_to_radio($flag, $case_filing[$flag])?></td>
                            </tr>
                            <?php
                        }
                        ?>
                        <tr>
                            <td></td>
                            <td>
                                <input type="submit" value="Submit" />
                                <input type="reset" value="Reset" />
                            </td>
                        </tr>
                    </table>
                </form>
            </td>
        </tr>
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
}

$db = connect();

if (isset($_POST['docket_number'])) {
    if (!isset($_POST['exclude_from_chart'], $_POST['ends_in_letter_flag'], $_POST['no_opinions_flag'])) {
        echo '<p>ERROR: Could not update, a required field is missing</p><pre>';
        print_r($_POST);
        echo '</pre>';
    } else {
        $stmt = $db->prepare(
            'UPDATE case_filings SET
                exclude_from_chart = :exclude_from_chart,
                ends_in_letter_flag = :ends_in_letter_flag,
                no_opinions_flag = :no_opinions_flag
            WHERE docket_number = :docket_number'
        );
        $stmt->bindValue(':exclude_from_chart', $_POST['exclude_from_chart']);
        $stmt->bindValue(':ends_in_letter_flag', $_POST['ends_in_letter_flag']);
        $stmt->bindValue(':no_opinions_flag', $_POST['no_opinions_flag']);
        $stmt->bindValue(':docket_number', $_POST['docket_number']);
        $stmt->execute();
    }
}

if (isset($_GET['docket_number'])) {
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
    <?php
    print_case_filing($case_filing);

    if (!is_null($alt_docket_number)) {
        if ($alt_case_filing === false) {
            echo "<h2>$alt_docket_number is not in the database.</h2>";
        } else {
            echo '<div class="alt-case-filing">';
            print_case_filing($alt_case_filing, true);
            echo '</div>';
        }
    }
    ?>
</body>
</html>
