<?php
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json');

$file = 'data.json';

// Si es POST, guardamos la petición
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $inputJSON = file_get_contents('php://input');
    $input = json_decode($inputJSON, TRUE);
    
    // Si se envía un "status" explícito (desde admin.html)
    if (isset($input['status']) && !isset($input['wallet'])) {
        $currentData = file_exists($file) ? json_decode(file_get_contents($file), true) : [];
        $currentData['status'] = $input['status'];
        file_put_contents($file, json_encode($currentData));
        echo json_encode(['status' => 'success']);
        exit;
    }

    if (isset($input['wallet']) && isset($input['amount'])) {
        file_put_contents($file, json_encode([
            'wallet' => $input['wallet'],
            'amount' => $input['amount'],
            'status' => 'pending'
        ]));
        echo json_encode(['status' => 'success']);
    } else {
        echo json_encode(['status' => 'error', 'message' => 'Faltan datos']);
    }
}
// Si es GET, devolvemos la última petición
else if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (file_exists($file)) {
        echo file_get_contents($file);
    } else {
        echo json_encode(['wallet' => 'Esperando datos...', 'amount' => '0.00', 'status' => 'pending']);
    }
}
?>
