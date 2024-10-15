"""
git_branch() {
    if [ -d .git ] || git rev-parse --git-dir > /dev/null 2>&1; then
        local branch_name=$(git branch 2>/dev/null | grep '^*' | colrm 1 2)

        if [ -n "$branch_name" ]; then
            echo "$branch_name"
        fi
    fi
}
# Command to visualize new addition to the current branch before pulling
# Excludes the svelte folder containing minified code
alias gdiff='git fetch && git diff $(git_branch) origin/$(git_branch) -- ":(exclude)app/webapp/static/svelte/"'
"""
