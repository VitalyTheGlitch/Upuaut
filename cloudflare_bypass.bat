@echo off

cls

color c

echo CLOUDFLARE BYPASS
echo.
echo Once the browser opens, open any request to Wolvesville.
echo Copy the "User-Agent" header and paste it into the environment file.
echo You can then close the browser and use the program.
echo.

pause

"C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="C:\Users\vital\AppData\Local\Google\Chrome\User Data\WolvesGod" wolvesville.com

color f
