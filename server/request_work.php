<?php
    require_once 'db.php';

    $rsQuery = $dbh->prepare("
            SELECT 	id, year, tif_number, url
            FROM	source_status
            WHERE 	status = 1
            LIMIT 1");
    // echo($query);
    $rsQuery->execute();

    $arResults = array();
    $count = 0;
    while($row = $rsQuery->fetch()) {
        $count++;
        $arRow = array();
        $arRow['year'] = $row['year'];
        $arRow['tif_number'] = $row['tif_number'];
        $arRow['url'] = $row['url'];
        $arResults[] = $arRow;

        // Update the DB with pending status
        $rsQuery2 = $dbh->prepare("
                UPDATE source_status set status = 2
                WHERE 	id = :id");
        // echo($query);
        $rsQuery2->bindParam(':id', $row['id'], PDO::PARAM_INT);
        $rsQuery2->execute();
    }
    if ($count == 0) {
        echo '[]';
    } else {
        echo json_encode($arResults);
    }
