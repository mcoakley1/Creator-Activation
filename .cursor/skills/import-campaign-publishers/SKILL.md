---
name: import-campaign-publishers
description: Assign a CSV of CreatorIQ publisher IDs to a campaign. Use when the user asks to import, add, upload, or assign publishers or creators to a CreatorIQ campaign, or provides a campaign id with a PublisherId list.
---

# Import publishers onto a CreatorIQ campaign

Use the repo script. Do not reimplement the HTTP calls, and do not print the API key.

## What the user must provide

- A campaign id
- A CSV with a `PublisherId` column (headers `Publisher Id` and `publisher_id` are equivalent)

If either is missing, ask for it. Do not guess a campaign id.

The default status is `Accepted`. Use another status only when the user asks. Allowed values are `Accepted`, `Invited`, `Selected`, and `Declined`.

## API key

Read the key from the environment, in this order:

1. `CREATORIQ_API_KEY`
2. `Uploading` (the CreatorIQ key injected in this cloud environment)

Send it only as the `x-api-key` header to `https://apis.creatoriq.com`. Never print the key, write it into the repo, or echo response bodies that contain it.

## Run

From the repository root:

```bash
python3 scripts/import_campaign_publishers.py --campaign CAMPAIGN_ID --csv PATH_TO_CSV
```

Add `--status Invited` only when the user wants a status other than `Accepted`.

Add `--dry-run` first only when the user asks to preview. When they ask to import or add the list, run it for real.

The script checks that the campaign exists, skips publishers already on that campaign, assigns the rest one at a time, and verifies each assignment.

## Report back

Include:

- Campaign id and campaign name
- Each publisher id with `added`, `already_on_campaign`, or `failed`
- Publisher name and status when CreatorIQ returns them
- The summary counts

A publisher who is already on the campaign is a success, not a failure. If any row failed, say which ids failed and include the API message with the key redacted. Do not assign anyone to a campaign the user did not name.
