---
date made: 2025-11-07
time made: 20:57
year: 2025
tags: 
- Fall2025
- CS370
aliases: ## Alternative terms for the doc
description: "This document contains the information about transferring and updating the web server files in the blue server"

## Categorizations.
isWork: true
isPersonal: true
isLearn: true
isCoursework: true
---
# Wagwan
- When i first tried to host the `cafcode` website on my own account I was having an issue where the `public_html` folder in the home directory was being accessed instead of the folder in the `Auction-Website` folder. To resolve this issue i moved the contents of the `public_html` in the `Auction-Website` folder to the home `public_html` folder and at first it did nothing but then i changed the permissions and it worked. 
- But now i had another issue where the changes i made to the `public_html` repo would not properly apply as the files needed to be moved out of the auctions folder to the home folder...
- The Idea I had was to ditch the git pull and instead `scp` the `public_html` folder to the blue account and then change its permissions. 

# Wagwan 2
- still had issue all the pages were not opening apparently, banged my head against the wall and asked AI for help apparently it was the line break that was the issue. Files modified in windows use DOS line break but Unix has a different one so had to use the dos2unix command to make my code work now that is done in the script as well.
  
# What to do from now on
First copy over the files from the local machine to blue like so.<br>
`{powershell} scp -r .\public_html\ rsharma@blue.cs.sonoma.edu:`
>Remember to be inside the `{powershell} .\Auction-Website` directory where the public html file resides.

After the files have been successfully moved to the Linux server run the script `setWebAccess.sh` in the home directory. <br>
This is a script that I created using chatGPT that assigns all the right permissions for web access. If script fails to run make sure the permissions are correct by running the following command `ls -l setWebAccess.sh` and see if the permissions match these 
<br> `{bash}-rwxr-xr-x 1 rsharma rsharma 674 Nov  7 20:49 setWebAccess.sh`

if they don't run this command `{bash}chmod +x setWebAccess.sh` <br>

```bash title:"Following are the contents of the script" fold:true
#!/bin/bash
# ==============================================================
# setWebAccess.sh
# Fixes permissions and converts Windows line endings for web access
# ==============================================================

PUBLIC_HTML=~/public_html

# --- Check folder exists ---
if [ ! -d "$PUBLIC_HTML" ]; then
    echo "Error: $PUBLIC_HTML does not exist."
    exit 1
fi

echo "Fixing permissions and line endings in $PUBLIC_HTML ..."

# --- Directory permissions ---
chmod 755 "$PUBLIC_HTML"
find "$PUBLIC_HTML" -type d -exec chmod 755 {} \;

# --- File permissions ---
find "$PUBLIC_HTML" -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" \) -exec chmod 644 {} \;
find "$PUBLIC_HTML" -type f \( -name "*.py" -o -name "*.cgi" -o -name "*.sh" \) -exec chmod 755 {} \;

# --- Convert Windows (CRLF) -> Unix (LF) line endings ---
echo "Running dos2unix cleanup..."
find "$PUBLIC_HTML" -type f \( -name "*.py" -o -name "*.cgi" -o -name "*.html" -o -name "*.css" -o -name "*.js" \) \
    -exec dos2unix -q {} \;

echo "✅ Permissions and line endings fixed successfully!"

```

# in Short
do this
on PC where we have the file
`{powershell} scp -r .\public_html\ rsharma@blue.cs.sonoma.edu:`
on the server
`{powershell} .\setWebAccess.sh`