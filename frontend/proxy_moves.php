<?php
header('Content-Type: application/json');

$idx = isset($_GET['idx']) ? (int)$_GET['idx'] : 0;
$url = "http://localhost:8000/legal_moves/$idx";

$ch  = curl_init($url);
curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_HTTPGET => true,]);

$resp = curl_exec($ch);
if ($resp === false) 
{
    http_response_code(502);
    echo json_encode(["error" => curl_error($ch)]);
    exit;
}

http_response_code(curl_getinfo($ch, CURLINFO_HTTP_CODE));
curl_close($ch);
echo $resp;