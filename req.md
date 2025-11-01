Product requirements

Purpose: Web app for managing vocabulary lists for learning foreign languages.

The app should allow me to upload words and phrases from CSV with the following attributes:

id: str: optional; opaque unique ID. If present, re-importing data uses this to associate with existing items. If omitted, importing data creates a new entry and generates a new ID.
lesson: str: optional; opaque lesson identifier (numbers, dates, labels) -- used to filter by lesson later.
front: str: front of the card, usually the foreign language
back: str: back of the card with the meaning
comment: str: optional extra information (can be empty), for example usage or grammar hints.
I want to be able to review vocabulary, allowing me to filter by lesson. The display should be in tabular form for now, and allow the following columns to be edited: front, back, comment, lesson.

The app should also allow me to export vocabulary to CSV.

The app also should offer shareable public links that offer a read-only view of vocabulary. These generated links should use a random token that is persisted and can be revoked. More than one sharable link can be generated at any time, and an overview table can be shown to the creator listing all shared links with an option to remove them.
