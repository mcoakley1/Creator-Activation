# Creator-Activation

## Import publishers onto a campaign

Save a CSV with a `PublisherId` column, then tell a Cursor agent the campaign id and attach the file:

> Import this list to campaign 2991466

The agent follows `.cursor/skills/import-campaign-publishers` and runs:

```bash
python3 scripts/import_campaign_publishers.py --campaign 2991466 --csv publishers.csv
```

The CreatorIQ API key stays in the environment (`CREATORIQ_API_KEY`, or the existing `Uploading` cloud secret). It is sent as the `x-api-key` header and is not stored in this repo.

Publishers already on the campaign are left in place. New publishers are added with status `Accepted` unless you pass `--status Invited`, `--status Selected`, or `--status Declined`. Add `--dry-run` to preview the change without assigning anyone.
