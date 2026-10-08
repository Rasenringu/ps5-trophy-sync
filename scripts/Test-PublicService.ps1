[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$origin = 'https://trophy-sync.party'
Add-Type -AssemblyName System.Net.Http
$handler = New-Object Net.Http.HttpClientHandler
$handler.AllowAutoRedirect = $false
$client = New-Object Net.Http.HttpClient($handler)
$client.Timeout = [TimeSpan]::FromSeconds(20)
try {
    foreach ($check in @(
        @{ Path='/api/health'; Method='GET'; Expected=200 },
        @{ Path='/api/auth/register'; Method='POST'; Expected=422 },
        @{ Path='/api/device/status'; Method='POST'; Expected=401 }
    )) {
        $request = New-Object Net.Http.HttpRequestMessage
        $request.Method = New-Object Net.Http.HttpMethod($check.Method)
        $request.RequestUri = $origin + $check.Path
        if ($check.Method -eq 'POST') {
            $request.Headers.Add('Origin', $origin)
            # Missing required fields: registration cannot create an account.
            $request.Content = New-Object Net.Http.StringContent('{}', [Text.Encoding]::UTF8, 'application/json')
        }
        $response = $client.SendAsync($request).GetAwaiter().GetResult()
        try {
            $status = [int]$response.StatusCode
            if ($status -ne $check.Expected) {
                throw "$($check.Path) returned $status; expected $($check.Expected). Check API WEB_ORIGIN, gateway routing and Cloudflare challenges."
            }
            Write-Host "PASS $($check.Path): $status"
        } finally { $response.Dispose(); $request.Dispose() }
    }
    Write-Host 'HTTPS/origin/routing checks passed. No account, installation, pairing or import created; no console validation.'
} finally { $client.Dispose(); $handler.Dispose() }
