#!/bin/sh
# Downloads the compile-only API jars into libs/ (gitignored). Run once before ./gradlew build.
set -e
cd "$(dirname "$0")"
mkdir -p libs
get() { [ -f "libs/$1" ] || { echo "Downloading $1"; curl -sfL -o "libs/$1" "$2"; }; }
get ftb-teams-neoforge-2101.1.11.jar   https://mediafilez.forgecdn.net/files/8724/782/ftb-teams-neoforge-2101.1.11.jar
get ftb-library-neoforge-2101.1.37.jar https://mediafilez.forgecdn.net/files/9008/89/ftb-library-neoforge-2101.1.37.jar
get SkyblockBuilder-21.1.37.jar        https://cdn.modrinth.com/data/por2AZc5/versions/NmXF6maO/SkyblockBuilder-21.1.37.jar
get LibX-1.21.1-6.0.15.jar             https://cdn.modrinth.com/data/qEH6GYul/versions/ADxNEmse/LibX-1.21.1-6.0.15.jar
echo "libs/ ready"
