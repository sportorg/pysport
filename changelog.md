# Changelog

# 2019-08-07 v1.5.0

+ Table refresh speed increased (comfortable work with >1000 rows)
+ Fast split printout (predefined standard template) with scaling
+ 2x2 relay support
+ SPORTident SRR Dongle support - touchless readout, intermediate
+ Merging punches while several readout
+ Split printout: added information, how many athletes can win current person
+ Athlete autocreate while readout (labyrinth)
+ Results by course
+ Results autoscroll
+ Search athlete by name while unknown chip readout
- Relays: set first leg finish as seond leg start etc.
- Improved SI-6 support
- Fixing in *.docx template for relays (last teams was missed)
* Data model was changed. Use exchange formats to downgrade (xml, wdb)

# 2019-01-18 v1.4.0

+ Added import of CourseData (courses) for IOF xml 
+ New status "Forced OK" to recover 
+ Mass edit possibility for selected athletes
- Calculating scores from leader time - ignoring mispunched athletes
- Team work data exchange format changed. Previous: `0{}1`, now: `{}`
- Search window freezing was fixed
 

# 2018-10-08 v1.3.0
+ Added MSP (mispunch) status, calculated by punches automatically
+ List or electronic cards to rent
+ Reduced row height in tables
+ Bib is stored in result even if athlete is deleted
+ Possibility of non-existing bib assigning for result
+ Reassigning results by bib
+ Reassigning results by card number
+ Import from another sportorg file
+ Result by score (rogain, free order with time limit, trail-o).
+ File auto-saving
+ Show quantity of results for each athlete
+ Jinja2 templates .docx (MS Word)
- Safe file saving (first write to file.sportorg.tmp, if it written correctly, rename to file.sportorg)
* Introduced custom scripts for online sending 

# 2018-06-13 v1.2.0

+ New JavaScript-based templates
+ Added new template (results_live) to manage DNF persons
+ "Rent" field it result table
+ Labyrinth mode, auto-define correct course  
+ Handicap. Calculation of start time from results
+ Multi day support
+ Dictionary of regions (file `regions.txt`) 
+ Dictionary of given names (file `names.txt`)
- Fixed error with last record in SFR card readout
- Fixed error with mixed toss (all athletes of course)

## 2018-04-24 v1.1.1

+ Added margins when printing

## 2018-04-17 v1.1.0

+ SFR (http://www.sportsystem.ru) timekeeping system support on Windows (only last model U5a with HID Interface). Thanks to Alexander Kurdumov for support and equipment sample.
+ Sportiduino (https://github.com/alexandervolikov/sportiduino) timekeeping system support. Thanks to Semyon Yakimov for contribution.
+ Sound effects while e-card readout
+ Auto filling of group and team if filter applied
+ Confirmation of application closing (including Alt+F4)
+ Detailed description of disqualification rules (Rus)
+ rufso-18-2. 'ZMS' qualification was removed (Rus)
+ rufso-18-10. Some translation changes (Rus)

- Fixed. Incorrect course order in relay printout
- Fixed. No ".json" extension while saving file on Linux

## 2018-03-16 v1.0.0

+ Official stable release
+ COM-port selecting for SPORTident master station

* Environment configuration for html templates
* Minor fixes in data model

## 2018-03-06 v0.11.0-rc4

+ Automatic disqualification if overtime
+ Templates improvement - information about course, location, time limit, referees was added
+ Team lists - added sorting by number and start time
+ Custom statuses for disqualification (external file)
+ Entry statistics report
+ Ranking for relays (Rus)
+ Saving of ranking information (Rus)

- Row braking in event title
- Relay online sending for orgeo.ru
- Simple finish support fixed (just finish time, F3)
- SI card editing fixed

## 2018-02-23 v0.11.0-rc3

+ SI Card assign mode
+ New templates for relay (start/result)
+ New storage format (.json)
+ Team work (client/server)
+ Editing person from result dialog
+ SI station status
+ Multi-language support
+ CP removing from courses and splits
+ Integration with Telegram

- Minor bug fixed
- Search fixed
- Online sending fixed

## 2018-01-25 v0.11.0-rc2

+ Fast start group editing (Alt + num)
+ Bulk DNS processing
+ New templates for splits and results
+ Partial relay support
+ Custom course order checking

- Minor buf fixed
- Saving with applied filter
- Stable sireader working (separated thread)

## 2018-01-16 v0.11.0-rc1

+ Added new field - id (uuid4)
+ Search tool - search text in all columns of current table
+ Creation organization while athlete editing
+ Team lists with start fee
+ Taking of start and finish time from any punch (by code)
+ Taking of start and finish from first and last punches
+ Live translation (to orgeo.ru)
+ Score calculation (formula and array)
+ Team result calculation by organization and region
+ Basic relay support (number assigning mode, place calculation)
+ Penalty calculation for marked route (Rus)
+ New Russian ranking ESVK 2018-2021 (Rus)

- Fixed the error of concurrent SI readout and split printing

## 2017-12-12 v0.10.0-beta

+ Added the ability to edit splits
+ Support for multiple marking systems at the model level
+ Printing of bib
+ Numbering rows in tables
+ Ability to select templates for separation
+ New template for split

- Taking into account the change in the starting time of the result

* Changed the project structure

## 2017-11-15 v0.9.0-beta

+ Assigning of card for athlete while result editing
+ Result editing - interactive number change
+ Person editing - check for duplicated bibs and card numbers
+ Improvements in SPORTident card readout
+ Rank calculation (specific for Russian orienteering)
+ Control order rechecking option
+ Automatic split reloading after course or bib change of result
+ Results tab: card number showing
+ Course editing: example of course control points configuration
+ Database format was changed - don't use files from previous version

- Default file names - date is moved to the first position
- Course: lap length saving was fixed
- Translation fixing for reports and interface
- Readout of cards with empty finish was fixed

## 2017-10-31 v0.8.0-beta

+ Automatical database saving while new finish or readout
+ Automatical SPORTident station connection
+ Remember the last used directory
+ Opening of recent file
+ Submenu "Recent files"
+ Templates (start list, results) were updated
+ Automatical split printing while readout

- "Open with" option for *.sportorg extention
- Mixing several groups while tossing
- Winorient import - splits import was fixed

## 2017-10-17 v0.7.2-beta

* Init
