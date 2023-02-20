# GitHub to Google Sheet

Isolated automation experiments to log all changes to a GitHub repository in a Google Sheet.

Overview:

- Set up Google Sheet with Apps Script [published as a web app](https://developers.google.com/apps-script/guides/web) - this allows it to respond to `GET` or `POST` requests.
- Add the URL of the Apps Script web app to the GitHub repository [as a secret](https://docs.github.com/en/actions/security-guides/encrypted-secrets) named `WEB_APP_URL`.
- Set up GitHub repository with a custom GitHub Action workflow to send a `POST` request to the Google Sheet web app whenever a push or other action is made on the repository.
- Have the Google Sheet web app parse the request and log the data into the sheet.
- Use Google Sheets App Scripts for any follow-up actions once the row is added.

- ... still trying to differentiate pull requests from pushes
