# gitcommitlogger

A Python package that logs the details of a specific set of commits made to a GitHub repository. Logs are saved into a `CSV` file and can optionally be sent in a request to a web app, such as a Google Apps Script attached to a Google Sheet where the data can be stored.

Overview:

- Set up Google Sheet with Apps Script [published as a web app](https://developers.google.com/apps-script/guides/web) - this allows it to respond to `GET` or `POST` requests.
- Add the URL of the Apps Script web app to the GitHub repository [as a secret](https://docs.github.com/en/actions/security-guides/encrypted-secrets) named `WEB_APP_URL`.
- The `logs-commits.yml` GitHub Action in this repository will send a `POST` request to the Google Sheet web app whenever a push is made on the repository.
- The web app will then add a row to the Google Sheet with the details of the commit, including the commit id, author, number of files changed in the commit, number of lines added and deleted.
