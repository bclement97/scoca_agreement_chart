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
    <h1>All Opinions</h1>
    <a href="index.php">Back to flagged case filings/opinions</a>
    <?php
    $db = connect();

    $opinions = $db->query(
        'SELECT id, docket_number, type_id, effective_type_id, authoring_justice, effective_type_flag, no_concurrences_flag
        FROM opinions
        ORDER BY id'
    );

    if (row_count($opinions)) {
        echo result_to_table($opinions, 'edit_opinion.php?%s=%s', 'id');
    } else {
        echo '<p>No opinions.</p>';
    }

    $db->close();
    ?>
</body>
</html>
