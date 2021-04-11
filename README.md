# BattlePokerAnalyzer

Tool for analyzing BattlePoker replays

The aim is to produce stats about the value of BattlePoker hands, and perhaps some visual charts or something

More data = more accurate results, let me know if you can share some replays ^^

Thank you to BotD and AMDG for providing a lot of replays already

## Current limitations

This is a work in progress so this current version has some limitations including:

* Only looks at 1 on 1 battles
* Doesn't account for card unit amounts
* Doesn't account for upgrades

## Sample outputs:

* TwoHandMatchups.csv - How much each specific hand wins against each specific hand
* TwoHandWinRatesByHand.csv - How much each hand wins against any hand
* WinRatesByIndividualUnit.csv - How much each unit type wins in whatever 2-card hand they're in against any 2-card hand
