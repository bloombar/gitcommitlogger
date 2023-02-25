/**
 * This is an example of a Google Apps Script that can receive commit logs in the form of JSON data sent with a POST request.
 * The script will log the data to a Google Sheet to which it is attached.
 * To implement this script, first create a new Google Sheet, and then click the `Extensions`->`Apps Script` menu item.  Paste the code there and click the button to `Deploy` a new version.
 * Once deployed, a public web app URL will be displayed where POST requests can be sent.
 */

const getConfig = () => {
  // global settings
  return {
    sheetName: "GitHub Logs",
    sheetFields: [
      "repository",
      "event",
      "id",
      "username",
      "email",
      "date",
      "message",
      "num_files",
      "num_additions",
      "num_deletions",
    ],
  }
}

const getSheet = () => {
  const config = getConfig()
  const ss = SpreadsheetApp.getActiveSpreadsheet() // container spreadsheet
  let sheet = ss.getSheetByName(config.sheetName) // specific worksheet
  if (sheet == null) {
    // create worksheet if none
    sheet = ss.insertSheet(config.sheetName)
    sheet.appendRow(config.sheetFields) // heading row
  }
  return sheet
}

function doGet(e) {
  const config = getConfig()
  const sheet = getSheet()
  const res = {
    type: "get",
    e: e,
  }
  sheet.appendRow([
    "get",
    "a man",
    "a plan",
    "panama",
    JSON.stringify(e.parameters, null, 3),
  ])
  console.log(JSON.stringify(res, null, 3))
  return ContentService.createTextOutput(res).setMimeType(
    ContentService.MimeType.JSON
  )
}

function doPost(e) {
  console.log("Incoming post request")
  console.log(JSON.stringify(e, null, 2))
  const sheet = getSheet()
  const res = {
    type: "post",
    e: e,
  }
  const commit_data = JSON.parse(e.postData.contents) // should be an array of objects
  if (Array.isArray(commit_data)) {
    for (let i = 0; i < commit_data.length; i++) {
      // log this commit!
      const commit = commit_data[i]
      console.log(JSON.stringify(commit, null, 2))
      // append data array to sheet as new row
      const row = [
        commit["repository_url"],
        commit["event_type"],
        commit["id"],
        commit["author_name"],
        commit["author_email"],
        commit["date"],
        commit["message"],
        commit["files"],
        commit["additions"],
        commit["deletions"],
      ]
      sheet.appendRow(row)
    }
    return ContentService.createTextOutput(commit_data).setMimeType(
      ContentService.MimeType.JSON
    )
  } else {
    return ContentService.createTextOutput(typeof commit_data).setMimeType(
      ContentService.MimeType.TEXT
    )
  }
}
