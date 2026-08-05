-- Launcher for NC Homestead Land Finder.
-- Starts Docker Desktop if needed, brings up the docker-compose stack,
-- waits for the frontend to respond, then opens it in the default browser.
--
-- Rebuild after editing this file:
--   osacompile -o ~/Desktop/"NC Homestead Land Finder.app" "Launch NC Homestead Land Finder.applescript"
--
-- Hardcoded absolute paths (docker, curl) because Finder-launched apps get
-- a minimal PATH that usually doesn't include /usr/local/bin.

set projectDir to "/Users/jonathanjones/AI-Property-Analyzer"
set dockerBin to "/usr/local/bin/docker"
set curlBin to "/usr/bin/curl"
set appTitle to "NC Homestead Land Finder"
set frontendURL to "http://localhost:5173"

-- 1. Make sure the Docker daemon is up (Docker Desktop must be installed).
set dockerReady to false
try
	do shell script quoted form of dockerBin & " info > /dev/null 2>&1"
	set dockerReady to true
end try

if not dockerReady then
	display notification "Starting Docker Desktop…" with title appTitle
	do shell script "/usr/bin/open -a Docker"
	repeat 60 times
		try
			do shell script quoted form of dockerBin & " info > /dev/null 2>&1"
			set dockerReady to true
			exit repeat
		end try
		delay 1
	end repeat
end if

if not dockerReady then
	display alert "Docker didn't start in time." message "Open Docker Desktop manually, wait for it to finish starting, then try again." as critical
	return
end if

-- 2. Bring up the stack.
display notification "Starting the app…" with title appTitle
try
	do shell script "cd " & quoted form of projectDir & " && " & quoted form of dockerBin & " compose up -d"
on error errText
	display alert "Failed to start the app." message errText as critical
	return
end try

-- 3. Wait for the frontend dev server to answer (first run installs npm
-- packages, so allow a couple of minutes).
set frontendReady to false
repeat 120 times
	try
		do shell script quoted form of curlBin & " -sf " & frontendURL & " > /dev/null"
		set frontendReady to true
		exit repeat
	end try
	delay 1
end repeat

if frontendReady then
	open location frontendURL
else
	display alert "The app is taking longer than expected to start." message "Check Docker Desktop's container logs, then try opening " & frontendURL & " manually." as warning
	open location frontendURL
end if
