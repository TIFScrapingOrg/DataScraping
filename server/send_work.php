<?php
    require_once 'db.php';

    // Make sure that this is a POST request
    
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        // Method not allowed
        http_response_code(405);
        echo "Method Not Allowed";
        return;
    }

    
    // Have all pieces been submitted?
    $cheese_submitted = isset($_FILES['cheese']);
    $butter_submitted = isset($_FILES['butter']);
    $bread_submitted = isset($_POST['bread']);
    if ( !($cheese_submitted && $butter_submitted && $bread_submitted) ) {
        echo 'Not all pieces submitted!';
        return;
    }


    // Check to see if the work being submitted is already completed
    // Extract record updates
    $sBread = $_POST['bread'];

    // JSON requires double quotes
    // Replace single quotes with double quotes
    $sBread = str_replace("'", '"', $sBread);

    $arCompletionRecords = json_decode($sBread);
    
    foreach ($arCompletionRecords as $record) {
        // Check if status is already 3
        $rsQueryCheck = $dbh->prepare("
            SELECT COUNT(*) as count
            FROM source_status
            WHERE tif_number = :tif
            AND year = :year
            AND status <> 3");
        $rsQueryCheck->bindParam(':tif', $record[1], PDO::PARAM_INT);
        $rsQueryCheck->bindParam(':year', $record[0], PDO::PARAM_INT);
        $rsQueryCheck->execute();
        $result = $rsQueryCheck->fetch(PDO::FETCH_ASSOC);
    
        if ($result['count'] == 0) {
            // Status is already 3, can't add data
            echo 'You have redundant data!';
            return;
        }
    }
    

    
    // CSV PROCESSING
    $csvYear = $arCompletionRecords[0][0];
    $tifNumb = $arCompletionRecords[0][1];

    $tifCsvName = 'uploads/' . $csvYear . '_' . $tifNumb . '.csv';
    // Move file
    move_uploaded_file( $_FILES['cheese']['tmp_name'], $tifCsvName);

    

    // JSON PROCESSING
    $uploadedFilePath = $_FILES['butter']['tmp_name'];
    $uploadedContent = file_get_contents($uploadedFilePath);
    $arNewData = json_decode($uploadedContent,true); 

    foreach ($arNewData as $year => $tif_object) {
        foreach ($tif_object as $tif_name => $tif_data) {
            $arExistingData[$year][$tif_name] = $tif_data;

            // Insert success record
            $sPageList =  implode(",", $tif_data['successful']);
            $rsQuery2 = $dbh->prepare("
                    INSERT INTO butter_json
                    (year, tif_number, successful, page_list)
                    VALUES (:year, :tif, 1, :page_list)");
            $rsQuery2->bindParam(':tif', $tif_name, PDO::PARAM_INT);
            $rsQuery2->bindParam(':page_list', $sPageList, PDO::PARAM_STR, 4000);
            $rsQuery2->bindParam(':year', $year, PDO::PARAM_INT);
            $rsQuery2->execute();

            // Insert failed record
            $sPageList =  implode(",", $tif_data['failed']);
            $rsQuery2 = $dbh->prepare("
                    INSERT INTO butter_json
                    (year, tif_number, successful, page_list)
                    VALUES (:year, :tif, 0, :page_list)");
            $rsQuery2->bindParam(':tif', $tif_name, PDO::PARAM_INT);
            $rsQuery2->bindParam(':page_list', $sPageList, PDO::PARAM_STR, 4000);
            $rsQuery2->bindParam(':year', $year, PDO::PARAM_INT);
            $rsQuery2->execute();
            
        }
    }
    

    // RECORD PROCESSING
    foreach ($arCompletionRecords as $record) {
        // Update the DB with pending status
        $rsQuery2 = $dbh->prepare("
                UPDATE source_status set status = 3
                WHERE 	tif_number = :tif
                    AND year = :year");
        $rsQuery2->bindParam(':tif', $record[1], PDO::PARAM_INT);
        $rsQuery2->bindParam(':year', $record[0], PDO::PARAM_INT);
        $rsQuery2->execute();
        // echo "UPDATES Year:" . $record[0] . " TIF:" . $record[1];
    }

    echo 'Records update successfully';

?>