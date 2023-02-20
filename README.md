# GitHub to Google Sheet

Isolated automation experiments to log all changes to a GitHub repository in a Google Sheet.

Overview:

- Set up Google Sheet with Apps Script [published as a web app](https://developers.google.com/apps-script/guides/web) - this allows it to respond to `GET` or `POST` requests.
- Set up GitHub repository with a custom GitHub Action workflow to send a `POST` request to the Google Sheet web app whenever a push or other action is made on the repository.
- Have the Google Sheet web app parse the request and log the data into the sheet.
- Use Google Sheets App Scripts for any follow-up actions once the row is added.
