$ErrorActionPreference = 'Stop'
$infraRoot = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
$buildDir = [IO.Path]::GetFullPath((Join-Path $infraRoot 'salesforce_web_build'))
if (-not $buildDir.StartsWith($infraRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Build output must remain inside the AskAnyDoc infra directory.'
}
if (Test-Path -LiteralPath $buildDir) { Remove-Item -LiteralPath $buildDir -Recurse -Force }
New-Item -ItemType Directory -Path $buildDir | Out-Null

$projectRoot = [IO.Path]::GetFullPath((Join-Path $infraRoot '..'))
$apiRequirements = Join-Path $projectRoot 'app/api/requirements.txt'
$linuxArgs = @('-t', $buildDir, '--platform', 'manylinux2014_x86_64', '--python-version', '3.13', '--implementation', 'cp', '--abi', 'cp313', '--only-binary=:all:', '--upgrade')

# Resolve MCP's cross-platform dependencies without asking Windows pip to fetch pywin32.
& pip install -r $apiRequirements 'httpx-sse>=0.4' 'jsonschema>=4.20' 'pydantic-settings>=2.5.2' 'pyjwt[crypto]>=2.10.1' 'python-multipart>=0.0.9' 'sse-starlette>=1.6.1' 'starlette>=0.27' 'uvicorn>=0.31.1' @linuxArgs
if ($LASTEXITCODE -ne 0) { throw 'Linux dependency build failed.' }
& pip install 'mcp==1.30.0' --no-deps @linuxArgs
if ($LASTEXITCODE -ne 0) { throw 'MCP SDK package build failed.' }

Copy-Item (Join-Path $projectRoot 'app/api/answer_lambda_handler.py'), (Join-Path $projectRoot 'app/api/assistant_orchestrator.py'), (Join-Path $projectRoot 'app/api/organisation_tools.py'), (Join-Path $projectRoot 'app/api/retrieval.py') $buildDir
foreach ($package in @('askanydoc_rag', 'sharepoint', 'salesforce')) {
    New-Item -ItemType Directory -Path (Join-Path $buildDir $package) | Out-Null
}
Copy-Item (Join-Path $projectRoot 'app/shared/askanydoc_rag/*.py') (Join-Path $buildDir 'askanydoc_rag')
Copy-Item (Join-Path $projectRoot 'app/sharepoint/*.py') (Join-Path $buildDir 'sharepoint')
Copy-Item (Join-Path $projectRoot 'app/salesforce/__init__.py'), (Join-Path $projectRoot 'app/salesforce/read_adapter.py'), (Join-Path $projectRoot 'app/salesforce/web_handler.py') (Join-Path $buildDir 'salesforce')
