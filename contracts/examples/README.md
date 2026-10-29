# contracts/examples

One accepted set of cards, laid out as meta_agent/ will be (profiles/, inbox/, requests/, knowledge/, cases/, harness/)
plus two bundle artifacts under bundle/. `python contracts/validate.py` judges them with the repository.
Every value is a fixture: commits are placeholders, sources are not real records, numbers are what the
fixture says and nothing more.

`rejected/` holds one folder per refusal the validator must make. Each folder has an `EXPECT` file naming
the check numbers that must FAIL, the offending card(s), and for checks 6 and 7 a `scenario.json` that
stands in for git. `python contracts/validate.py --expect-fail` runs them and prints two totals: fixtures
rejected and expected checks rejected. Both must be complete.
