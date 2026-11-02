# FIN2: replicate of the final evaluation (pre-registered 2 Nov 2026)

**Purpose.** FIN (D-056) was one run per arm. This replicates every arm once more to show how far a second run moves the numbers. Written before the runs started.

**Setup.** Same corpus (v3.1), same code and prompts as FIN, both models (`gpt-6-luna`, `gpt-5.6-luna`), `r3` and `hybrid`, planner prompt `planner_v1`, answer prompt `answer_v3`, judge `gpt-6.1-terra`. Sets: development 237, registered 31, fresh 65. New experiment ids `agent-dev-FIN2-*`, `agent-heldout-FIN2-*`, `agent-heldout-FIN2V2-*`. FIN files are not touched.

**What will be reported, whatever the result.** Behaviour accuracy per arm for both runs side by side, the paired `r3` minus `hybrid` difference for the replicate, and the largest run-to-run change for any arm. FIN and FIN2 are shown side by side.

**Not claimed.** Two runs are still too few to give a variance estimate. The development questions shaped the design. The fresh questions were already known.

**Amendment, 2 Nov 2026, made on the owner's instruction before any FIN2 result was scored or read (generation was under way).** The headline is the mean of the two runs per arm, not FIN alone. Paired differences use each case's mean outcome over the two runs (0, 0.5 or 1), with the same case bootstrap (10000 resamples, seed 20261030). Both single runs stay visible next to the mean. If the two runs disagree on the sign of a paired difference, the mean is reported as unresolved. Cost, latency and over-abstention are also means of the two runs.
