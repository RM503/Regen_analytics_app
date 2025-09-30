#!/bin/bash
# Use script to automate git pushes to desired branch - scripts/git_commit.sh

msg=$1 # first argument
branch=$2 # second argument

shift 2

files=$@ # list of files to commit

# If no files are passed, add all (git add .)
if [ -z $files ]; then
    files="."
fi

git add $files
git commit -m "$msg"
git push origin "$branch"