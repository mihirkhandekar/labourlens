# Fresh-clone check

How a clone of this repository behaves without the private corpus, and what was observed.

Procedure: `git clone <this repository> /tmp/<dir>`, check out the branch, then `make setup && make verify` in the clone. No `.env`, no `data/raw`, `data/passages` or `data/index`, no API key.
