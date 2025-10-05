@echo off
echo Building test container...
docker build -t pytest-container .
echo Running tests in isolated container...
docker run --rm --env-file .env ^
  -v "%cd%\test_output:/app/test_output" ^
  -v "%cd%\temp_files:/app/temp_files" ^
  -v "%cd%\storage:/app/storage" ^
  -v "%cd%\logs:/app/logs" pytest-container
pause
