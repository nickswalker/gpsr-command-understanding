<?php
if (isset($_SERVER['HTTP_ORIGIN'])) {
    header("Access-Control-Allow-Origin: {$_SERVER['HTTP_ORIGIN']}");
    header('Access-Control-Allow-Credentials: true');
    header('Access-Control-Max-Age: 86400'); // cache for 1 day

}
// Access-Control headers are received during OPTIONS requests
if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    if (isset($_SERVER['HTTP_ACCESS_CONTROL_REQUEST_METHOD'])) {
        header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
    }
    if (isset($_SERVER['HTTP_ACCESS_CONTROL_REQUEST_HEADERS'])) {
        header("Access-Control-Allow-Headers: {$_SERVER['HTTP_ACCESS_CONTROL_REQUEST_HEADERS']}");
    }
    exit(0);
}
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
// Make sure CORS allow is working
//curl -H "Origin: http://localhost:8000" --verbose https://mturk.nickwalker.us/spoken-commands/upload.php
echo var_dump($_FILES);
echo var_dump($_REQUEST);
$data = file_get_contents($_FILES['audio']['tmp_name']);

$name= $_REQUEST["name"];
$name = mb_ereg_replace("([^\w\s\d\-_~,;\[\]\(\).])", '', $name);
// Remove any runs of periods (thanks falstro!)
$name = mb_ereg_replace("([\.]{2,})", '', $name);
$fp = fopen("saved_audio/" . $name. '.ogg', 'wb') or die("Unable to open file");

fwrite($fp, $data);
fclose($fp);
echo "Success";
http_response_code(200);