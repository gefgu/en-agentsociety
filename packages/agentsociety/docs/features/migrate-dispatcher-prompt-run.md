# Run Tracking: Migrate BlockDispatcher away from FormatPrompt / prompt.py

## Plan

- [x] Step 1: Read prompt.py to understand FormatPrompt
- [x] Step 2: Read dispatcher.py to understand FormatPrompt usage
- [x] Step 3: Grep codebase to confirm dispatcher is the only runtime user
- [x] Step 4: Create TOML prompt entry for dispatcher prompt
- [x] Step 5: Update dispatcher.py to use PromptManager
- [ ] Step 6: Verify dispatcher.py is fully functional (review)
- [ ] Step 7: Confirm no other file imports from prompt.py
- [ ] Step 8: Delete prompt.py

## Commits
- Commit 1: Add TOML + update dispatcher.py
- Commit 2: Delete prompt.py
