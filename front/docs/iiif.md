# IIIF usage in app

## Witness and Series

The Witness is the main entity of the database, it represents one unique physical document
(a manuscript, a printed document, a letter, etc.). In short, a Series is a collection of
Witnesses: they are grouped in a Series if they share a common history of creation and conservation
(e.g. a collection of letters kept in the same library, all encyclopedia volumes held by the Académie des Sciences, etc.)

## Digitization

Each Witness, as a physical object, may have been digitized one or several times.
In the app, we consider each Digitization as a proper object, independent of its Witness.
Thus, a Witness can be linked to multiple Digitizations (a microfilm, a HD scan, etc.).
