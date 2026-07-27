# test_endpoints.ps1
$baseUrl = "http://127.0.0.1:8000"

function Test-Endpoint {
    param (
        [string]$Name,
        [scriptblock]$Action
    )
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Testing: $Name" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    try {
        $response = &$Action
        $response | ConvertTo-Json -Depth 10 | Write-Host
        Write-Host "[SUCCESS] $Name" -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] Failed to execute request." -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        if ($_.ErrorDetails -ne $null) {
            Write-Host "Response Body: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        }
    }
}

# 1. Health Check
Test-Endpoint -Name "/health" -Action {
    Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
}

# 2. Structured Query (No LLM generation)
Test-Endpoint -Name "/query/structured (Filters only)" -Action {
    $uri = "$baseUrl/query/structured?category=Nature&max_fee=1500&generate_answer=false"
    Invoke-RestMethod -Uri $uri -Method Get
}

# 3. Structured Query (With LLM Generation)
Test-Endpoint -Name "/query/structured (With RAG)" -Action {
    $uri = "$baseUrl/query/structured?district=Kandy&generate_answer=true&question=What%20can%20I%20do%20here%3F"
    Invoke-RestMethod -Uri $uri -Method Get
}

# 4. Semantic Query (With LLM Generation)
Test-Endpoint -Name "/query/semantic" -Action {
    $uri = "$baseUrl/query/semantic?query=beautiful%20waterfall%20for%20swimming&top_k=2&generate_answer=true"
    Invoke-RestMethod -Uri $uri -Method Get
}

# 5. Image Query (Using text_query as a Multipart Form)
# Test-Endpoint -Name "/query/image (Text describing an image)" -Action {
#     $form = @{
#         text_query = "ancient buddhist temple ruins"
#         top_k = "2"
#         generate_answer = "true"
#         question = "Summarize the history of these sites."
#     }
#     Invoke-RestMethod -Uri "$baseUrl/query/image" -Method Post -Form $form
# }

# Note: To test an actual file upload for the /query/image endpoint in PowerShell, 
# you would adjust the form hashtable like this:
# $form = @{
#     file = Get-Item -Path ".\path\to\test_image.jpg"
#     generate_answer = "false"
# }