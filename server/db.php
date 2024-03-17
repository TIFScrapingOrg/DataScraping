<?php
/*** mysql hostname ***/
$hostname = '127.0.0.1';

/*** mysql database ***/
$dbname = 'noahbaxley_TIF_Project';

/*** mysql username ***/
$username = 'noahbaxley_tif_project_user';

/*** mysql password ***/
$password = '_&C,4Q?_Rt$+';

try {
	$dbh = new PDO("mysql:host=$hostname;dbname=$dbname", $username, $password);
	//	$dbh = new PDO("mysql:host=$hostname;dbname=listmaker", $username, $password);
	/*** echo a message saying we have connected ***/
	//echo 'Connected to database<br />';

	/*** set the error reporting attribute ***/
	$dbh->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
}
catch(PDOException $e){
	echo $e->getMessage();
}

?>