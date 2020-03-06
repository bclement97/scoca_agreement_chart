<?php
require_once 'lib/db.php';
require_once 'lib/html.php';

$db = connect();
/*
 * The flagged case filings' ordering below (no_opinions_flag DESC, ends_in_letter_flag)
 * reveals an interesting relationship between the docket numbers and the flags.
 *
 * - S######:   no_opinions_flag = 1 AND ends_in_letter_flag = 0
 * - S######M:  no_opinions_flag = 1 AND ends_in_letter_flag = 1
 * - S######A:  no_opinions_flag = 0 AND ends_in_letter_flag = 0
 */
$flagged_case_filings = $db->query(<<<'SQL'
SELECT docket_number, url, sha1, filed_on, added_on, no_opinions_flag, ends_in_letter_flag
FROM case_filings 
WHERE ends_in_letter_flag = 1 OR no_opinions_flag = 1
ORDER BY no_opinions_flag DESC, ends_in_letter_flag, filed_on, added_on
SQL
);
$flagged_opinions = $db->query(<<<'SQL'
SELECT id, docket_number, type_id, effective_type_id, authoring_justice, effective_type_flag, no_concurrences_flag
FROM opinions
WHERE no_concurrences_flag = 1 OR effective_type_flag = 1
ORDER BY effective_type_flag DESC, no_concurrences_flag DESC, docket_number, type_id, effective_type_id
SQL
);
?>

<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="styles/index.css">
</head>
<body>
    <h1>SCOCA Agreement Chart Admin Interface</h1>

    <h2>Flagged Case Filings</h2>
    <?php
    if (row_count($flagged_case_filings)) {
        echo result_to_table($flagged_case_filings, 'edit_case_filing.php?%s=%s', 'docket_number');
    } else {
        echo '<p>No flagged case filings.</p>';
    }
    ?>

    <h2>Flagged Opinions</h2>
    <?php
    if (row_count($flagged_opinions)) {
        echo result_to_table($flagged_opinions, 'edit_opinion.php?%s=%s', 'id');
    } else {
        echo '<p>No flagged opinions.</p>';
    }

    $db->close();
    ?>
</body>
</html>
