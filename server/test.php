<?php
    $arTest[] = [2018, 1];
    $arTest[] = [2018, 2];
    $arTest[] = [2018, 3];

    $sTest = json_encode($arTest);

    $arNew = json_decode($sTest);
    print_r($arNew);