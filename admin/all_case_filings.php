<?php
require_once 'lib/db.php';
require_once 'lib/html.php';
?>

<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="styles/index.css">
</head>
<body>
    <h1>All Case Filings</h1>
    <a href="index.php">Back to flagged case filings/opinions</a>
    <?php
    $db = connect();

    $case_filings = $db->query(
        'SELECT docket_number, url, sha1, filed_on, added_on, no_opinions_flag, ends_in_letter_flag
        FROM case_filings
        ORDER BY filed_on DESC, added_on DESC, docket_number'
    );

    if (row_count($case_filings)) {
        echo result_to_table($case_filings, 'edit_case_filing.php?%s=%s', 'docket_number');
    } else {
        echo '<p>No case filings.</p>';
    }

    $db->close();
    ?>
</body>
</html>
